#!/usr/bin/env python3
"""Sendet Web-Push wenn data/tipps/*.json aktualisiert wurde.
Wird via GitHub Actions getriggert (Bridge zwischen Cloud-Routine und Apple Push Service).
"""
import os, json, glob
from pywebpush import webpush, WebPushException

# Neuestes Tipps-File finden
files = sorted(glob.glob('data/tipps/*.json'))
if not files:
    print("Kein tipps-File gefunden")
    exit(0)

latest = files[-1]
print(f"Lese: {latest}")
with open(latest, encoding='utf-8') as f:
    data = json.load(f)

datum = data.get('datum', '?')
n_spiele = len(data.get('spiele', []))
n_einzel = len(data.get('einzeltipps', []))
n_kombi = len(data.get('kombis', []))

# Risiko-Kombi-Quote suchen
risiko_quote = None
for k in data.get('kombis', []):
    name_lower = (k.get('name', '') + k.get('id', '')).lower()
    if 'risiko' in name_lower or 'risk' in name_lower:
        risiko_quote = k.get('gesamtquote')
        break

# Highlight aus erstem SAFE-Einzeltipp
highlight = None
for e in data.get('einzeltipps', []):
    if e.get('kategorie', '').lower() == 'safe':
        highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"
        break
if not highlight and data.get('einzeltipps'):
    e = data['einzeltipps'][0]
    highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"

# Body bauen
parts = [f"{n_spiele} Spiele", f"{n_einzel} Tipps"]
if highlight:
    parts.append(f"Top: {highlight}")
if risiko_quote:
    parts.append(f"Risiko {risiko_quote}x")
body = " · ".join(parts)
if len(body) > 120:
    body = body[:117] + "..."

print(f"Body: {body}")

# Push senden
sub_str = os.environ.get('PUSH_SUB', '').strip()
if not sub_str:
    print("FEHLER: PUSH_SUB Secret fehlt")
    exit(1)
sub = json.loads(sub_str)

vapid = os.environ.get('VAPID_PRIVATE', '').strip()
if not vapid:
    print("FEHLER: VAPID_PRIVATE Secret fehlt")
    exit(1)

payload = json.dumps({
    'title': '🐚 Neue Tipps verfügbar',
    'body': body,
    'url': 'https://melvinhooo.github.io/miesmuschel/',
    'tag': 'miesmuschel-tipps'
})

for attempt in range(3):
    try:
        r = webpush(
            subscription_info=sub,
            data=payload,
            vapid_private_key=vapid,
            vapid_claims={'sub': 'mailto:msejdiu@b-dhilden.de'}
        )
        print(f"Push gesendet, status {r.status_code}")
        break
    except WebPushException as e:
        print(f"Versuch {attempt+1} fehlgeschlagen: {e}")
        if e.response:
            print(f"Response: {e.response.text}")
        if attempt == 2:
            print("Alle 3 Versuche fehlgeschlagen")
            exit(1)
