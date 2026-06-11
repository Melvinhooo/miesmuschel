#!/usr/bin/env python3
"""Anstoß-Reminder-Dispatcher (10.06.2026 WM-Setup).

Läuft alle 15 Min via GitHub Action. Pro Lauf:
1. Lese data/tipps/<heute>.json + data/tipps/<gestern>.json
   (gestern auch nötig weil späte Spiele mit Anstoß 04:00 Berlin am Folgetag liegen)
2. Für jedes Spiel: berechne Minuten bis Anstoß
3. Wenn Anstoß in 60-90 Min UND noch kein Reminder gesendet:
   sende iOS-Push mit Top-Tipp + tracke in data/reminders/<datum>.json

Reminder-Tracking-File-Schema:
{
  "stand": "ISO-Timestamp",
  "gesendet": {
    "<spiel_id>": {"sent_at": "ISO", "anstoss": "ISO", "spiel": "X vs Y"}
  }
}
"""
import os, sys, json, glob, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIPPS_DIR = ROOT / 'data' / 'tipps'
REM_DIR = ROOT / 'data' / 'reminders'
REM_DIR.mkdir(parents=True, exist_ok=True)

# Berlin-Zeitzone manuell (MESZ Sommer): +2h zu UTC
# Falls Cron-Spitze 25.10. DST-Wechsel: dann auf MEZ +1h schalten
BERLIN_OFFSET = timedelta(hours=2)

# Reminder-Fenster: Anstoß muss in 60-90 Min sein (Standard).
# Bei sehr späten Spielen (z.B. 04:00 Berlin) reicht auch 30-60 Min.
WINDOW_MIN_MIN = 30
WINDOW_MAX_MIN = 90


def now_berlin():
    return datetime.now(timezone.utc) + BERLIN_OFFSET


def lade_tipps_files():
    """Lese heute + gestern (für späte Spiele mit Anstoß-Folgetag-Berlin)."""
    heute = now_berlin().date()
    gestern = heute - timedelta(days=1)
    files = []
    for d in (gestern, heute):
        p = TIPPS_DIR / f'{d.isoformat()}.json'
        if p.exists():
            try:
                with open(p, encoding='utf-8') as f:
                    files.append((d, json.load(f)))
            except (json.JSONDecodeError, OSError):
                pass
    return files


def lade_reminder_tracker(datum):
    p = REM_DIR / f'{datum.isoformat()}.json'
    if p.exists():
        try:
            with open(p, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {'stand': now_berlin().isoformat(), 'gesendet': {}}


def speichere_reminder_tracker(datum, tracker):
    p = REM_DIR / f'{datum.isoformat()}.json'
    tracker['stand'] = now_berlin().isoformat()
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def parse_anstoss(anstoss_str):
    """Parse ISO-Datetime mit Timezone und konvertiere zu Berlin-Zeit."""
    if not anstoss_str:
        return None
    try:
        # Format z.B. "2026-06-11T21:00:00+02:00" oder "2026-06-12T04:00:00+02:00"
        s = anstoss_str.strip()
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        # Python 3.11+ akzeptiert +02:00 direkt
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # Annahme: Berlin
            dt = dt.replace(tzinfo=timezone(BERLIN_OFFSET))
        # Konvertiere zu Berlin
        return dt.astimezone(timezone(BERLIN_OFFSET))
    except (ValueError, TypeError):
        return None


def get_top_tipp_fuer_spiel(daten, spiel_id):
    """Suche den höchst-priorisierten Tipp für ein Spiel.
    Priorität: SAFE > VALUE > WACKEL > erster Einzeltipp.
    """
    KAT_PRIO = {'safe': 0, 'value': 1, 'wackel': 2, 'risk': 3, 'moonshot': 4}
    kandidaten = [e for e in daten.get('einzeltipps', []) if e.get('spiel_id') == spiel_id]
    if not kandidaten:
        # Fallback: tipps[] des Spiels durchsuchen
        for s in daten.get('spiele', []):
            if s.get('id') == spiel_id:
                for t in s.get('tipps', []):
                    kandidaten.append({
                        'kategorie': t.get('kategorie', ''),
                        'markt': t.get('markt', ''),
                        'quote': t.get('quote'),
                    })
                break
    if not kandidaten:
        return None
    kandidaten.sort(key=lambda e: KAT_PRIO.get((e.get('kategorie') or '').lower(), 9))
    return kandidaten[0]


def trigger_push(title, body, tag_suffix):
    """Rufe send_push.py im reminder-Modus über Env-Vars auf."""
    env = os.environ.copy()
    env['REMINDER_TITLE'] = title
    env['REMINDER_BODY'] = body
    env['REMINDER_TAG'] = tag_suffix
    script = ROOT / '.github' / 'scripts' / 'send_push.py'
    r = subprocess.run(['python3', str(script), 'reminder'],
                       env=env, capture_output=True, text=True, cwd=str(ROOT))
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    return r.returncode == 0


def main():
    now = now_berlin()
    print(f'Reminder-Dispatcher: jetzt {now.isoformat()}')

    tipps_files = lade_tipps_files()
    if not tipps_files:
        print('Keine Tipps-Files gefunden.')
        return 0

    anzahl_pushs = 0
    for datum_file, daten in tipps_files:
        tracker = lade_reminder_tracker(datum_file)
        gesendet = tracker.get('gesendet', {})
        modified = False

        for s in daten.get('spiele', []):
            spiel_id = s.get('id')
            if not spiel_id:
                continue
            if spiel_id in gesendet:
                continue  # Schon Reminder gesendet
            anstoss = parse_anstoss(s.get('anstoss'))
            if not anstoss:
                continue
            minuten_bis = (anstoss - now).total_seconds() / 60
            if not (WINDOW_MIN_MIN <= minuten_bis <= WINDOW_MAX_MIN):
                continue

            top = get_top_tipp_fuer_spiel(daten, spiel_id)
            heim = s.get('heim', '?')
            gast = s.get('gast', '?')
            title = f'🐚 {heim} vs {gast} in {int(minuten_bis)}min'
            if top:
                kat = (top.get('kategorie') or '').upper()
                markt = top.get('markt', '?')
                quote = top.get('quote')
                if quote:
                    body = f'Dein {kat}: {markt} @ {quote}'
                else:
                    body = f'Dein {kat}: {markt}'
            else:
                body = 'Spielbeginn naht'

            # tag_suffix: kompakt + spiel_id (für eindeutige iOS-Push-Sortierung)
            tag = spiel_id.replace('-', '')[:30]
            ok = trigger_push(title, body, tag)
            if ok:
                gesendet[spiel_id] = {
                    'sent_at': now.isoformat(),
                    'anstoss': anstoss.isoformat(),
                    'spiel': f'{heim} vs {gast}',
                    'top_tipp': top.get('markt', '?') if top else None,
                }
                modified = True
                anzahl_pushs += 1
                print(f'  Reminder gesendet: {heim} vs {gast} in {int(minuten_bis)}min')

        if modified:
            tracker['gesendet'] = gesendet
            speichere_reminder_tracker(datum_file, tracker)

    print(f'OK: {anzahl_pushs} Reminder gesendet.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
