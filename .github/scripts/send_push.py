#!/usr/bin/env python3
"""Sendet Web-Push wenn data/tipps/*.json, data/ergebnisse/*.json,
data/tipps_wochenende/*.json oder data/tipps_woche/*.json aktualisiert wurde.
Wird via GitHub Actions getriggert (Bridge zwischen Cloud-Routine und Apple Push Service).

Aufruf:
  python send_push.py tipps        # Push fuer neue Tages-Tipps
  python send_push.py auswertung   # Push fuer Tages-Auswertung
  python send_push.py wochenende   # Push fuer Wochenend-Vorschau
  python send_push.py woche        # Push fuer Wochen-Vorschau
"""
import os, sys, json, glob
from pywebpush import webpush, WebPushException


def build_tipps_payload():
    files = sorted(glob.glob('data/tipps/*.json'))
    if not files:
        return None
    latest = files[-1]
    print(f"Lese Tipps: {latest}")
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)

    n_spiele = len(data.get('spiele', []))
    n_einzel = len(data.get('einzeltipps', []))

    risiko_quote = None
    for k in data.get('kombis', []):
        name_lower = (k.get('name', '') + k.get('id', '')).lower()
        if 'risiko' in name_lower or 'risk' in name_lower:
            risiko_quote = k.get('gesamtquote')
            break

    highlight = None
    for e in data.get('einzeltipps', []):
        if e.get('kategorie', '').lower() == 'safe':
            highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"
            break
    if not highlight and data.get('einzeltipps'):
        e = data['einzeltipps'][0]
        highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"

    parts = [f"{n_spiele} Spiele", f"{n_einzel} Tipps"]
    if highlight:
        parts.append(f"Top: {highlight}")
    if risiko_quote:
        parts.append(f"Risiko {risiko_quote}x")
    body = " · ".join(parts)
    if len(body) > 120:
        body = body[:117] + "..."

    return {
        'title': '🐚 Neue Tipps verfügbar',
        'body': body,
        'tag': 'miesmuschel-tipps',
    }


def _build_dossier_payload(glob_pattern, title, label):
    """Generischer Builder fuer Tipps-aehnliche Dossiers (Wochenende, Woche, Tag)."""
    files = sorted(glob.glob(glob_pattern))
    if not files:
        return None
    latest = files[-1]
    print(f"Lese {label}: {latest}")
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)

    n_spiele = len(data.get('spiele', []))
    n_einzel = len(data.get('einzeltipps', []))

    risiko_quote = None
    for k in data.get('kombis', []):
        name_lower = (k.get('name', '') + k.get('id', '')).lower()
        if 'risiko' in name_lower or 'risk' in name_lower:
            risiko_quote = k.get('gesamtquote')
            break

    highlight = None
    for e in data.get('einzeltipps', []):
        if e.get('kategorie', '').lower() == 'safe':
            highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"
            break
    if not highlight and data.get('einzeltipps'):
        e = data['einzeltipps'][0]
        highlight = f"{e.get('markt', '')} @{e.get('quote', '?')}"

    parts = [f"{n_spiele} Spiele", f"{n_einzel} Tipps"]
    if highlight:
        parts.append(f"Top: {highlight}")
    if risiko_quote:
        parts.append(f"Risiko {risiko_quote}x")
    body = " · ".join(parts)
    if len(body) > 120:
        body = body[:117] + "..."

    return {
        'title': title,
        'body': body,
        'tag': f"miesmuschel-{label}",
    }


def build_wochenende_payload():
    return _build_dossier_payload(
        'data/tipps_wochenende/*.json',
        '🐚 Wochenend-Vorschau',
        'wochenende',
    )


def build_woche_payload():
    return _build_dossier_payload(
        'data/tipps_woche/*.json',
        '🐚 Wochen-Vorschau',
        'woche',
    )


def build_auswertung_payload():
    """Push-Payload fuer Tages-Auswertung. Liest neuestes ergebnisse/*.json."""
    files = sorted(glob.glob('data/ergebnisse/*.json'))
    if not files:
        return None
    latest = files[-1]
    print(f"Lese Auswertung: {latest}")
    with open(latest, encoding='utf-8') as f:
        data = json.load(f)

    datum = data.get('datum', '?')

    # Einzeltipp-Bilanz
    et_results = data.get('einzeltipps_ergebnis') or []
    et_won = sum(1 for e in et_results if e.get('status') == 'gewonnen')
    et_total = len(et_results)

    # Kombi-Bilanz
    k_results = data.get('kombis_ergebnis') or []
    k_won = sum(1 for k in k_results if k.get('status') == 'gewonnen')
    k_total = len(k_results)

    # Netto-Profit aus tipps_ergebnis (gewinn_faktor pro 1u)
    netto = 0.0
    for spiel in data.get('spiele', []):
        for tr in spiel.get('tipps_ergebnis', []) or []:
            try:
                netto += float(tr.get('gewinn_faktor') or 0)
            except (TypeError, ValueError):
                pass
    netto_str = f"{netto:+.2f}U"

    parts = [f"Bilanz {datum}"]
    if et_total:
        parts.append(f"Einzel {et_won}/{et_total}")
    if k_total:
        parts.append(f"Kombi {k_won}/{k_total}")
    parts.append(netto_str)
    body = " · ".join(parts)
    if len(body) > 120:
        body = body[:117] + "..."

    return {
        'title': '🐚 Auswertung fertig',
        'body': body,
        'tag': 'miesmuschel-auswertung',
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'tipps'
    print(f"Mode: {mode}")

    if mode == 'auswertung':
        payload_dict = build_auswertung_payload()
    elif mode == 'wochenende':
        payload_dict = build_wochenende_payload()
    elif mode == 'woche':
        payload_dict = build_woche_payload()
    else:
        payload_dict = build_tipps_payload()

    if not payload_dict:
        print("Keine Daten gefunden, Push uebersprungen")
        return 0

    payload_dict['url'] = 'https://melvinhooo.github.io/miesmuschel/'
    print(f"Body: {payload_dict['body']}")

    sub_str = os.environ.get('PUSH_SUB', '').strip()
    if not sub_str:
        print("FEHLER: PUSH_SUB Secret fehlt")
        return 1
    sub = json.loads(sub_str)

    vapid = os.environ.get('VAPID_PRIVATE', '').strip()
    if not vapid:
        print("FEHLER: VAPID_PRIVATE Secret fehlt")
        return 1

    payload = json.dumps(payload_dict)

    for attempt in range(3):
        try:
            r = webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=vapid,
                vapid_claims={'sub': 'mailto:msejdiu@b-dhilden.de'}
            )
            print(f"Push gesendet, status {r.status_code}")
            return 0
        except WebPushException as e:
            print(f"Versuch {attempt+1} fehlgeschlagen: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            if attempt == 2:
                print("Alle 3 Versuche fehlgeschlagen")
                return 1


if __name__ == '__main__':
    sys.exit(main())
