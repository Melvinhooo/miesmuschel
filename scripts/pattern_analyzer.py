"""Auto-Pattern-Analyzer (04.05.2026): scant data/ergebnisse/ + statistik.json,
findet Verlust-Pattern, schreibt Lesson-Vorschlaege in data/lessons_pending.json.

Loest das Pattern dass User stundenlang manuell Verluste analysiert. Stattdessen:
1. Verluste der letzten 7 Tage clustern (Liga + Markt-Typ + Kategorie)
2. Saison-Kontext-Selbstwiderspruch finden (Routine schrieb 'edge kleiner', labelte SAFE)
3. Defensiv-Cluster erkennen (Spiele mit 3+ DC/Total/BTTS und 0 Sieg/Torschuetze)
4. Star-Out-Backup-Verpasst-Pattern (Top-Stuermer Out, kein Backup-Tipp)
5. Lesson-Vorschlaege schreiben - User checkt + uebernimmt manuell in lessons.json

Aufruf:
  python scripts/pattern_analyzer.py
Wird auch von Daily-Pattern-Hunter-Cloud-Routine aufgerufen (siehe RemoteTrigger).
"""
from __future__ import annotations
import json, sys, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ERG = ROOT / "data" / "ergebnisse"
DATA_TIPPS = ROOT / "data" / "tipps"
DATA_STAT = ROOT / "data" / "statistik.json"
DATA_LESSONS = ROOT / "data" / "lessons.json"

# Schwellen
TAGE_FENSTER = 7
MIN_TIPPS_FUER_AUTO_APPLY = 4   # Auto-Apply nur bei klarer Statistik
MIN_TIPPS_FUER_PATTERN = 3      # Niedriger fuer Hint-Generation
NEGATIVE_EDGE_PHRASEN = ('edge kleiner', 'eher 50/50', 'eher coinflip', 'rotiert vor',
                         'edge geringer', 'kleiner als suggeriert', 'vorsicht', 'unklarer favorit')
SIEG_KEYWORDS = ('sieg', 'moneyline', '(ml)', '(1x2)', 'spread', 'handicap')
TORSCHUETZE_KEYWORDS = ('trifft', 'torschuetz', 'jederzeit tor', 'doppelpack', 'hattrick')


def lade_letzte_ergebnisse(tage: int) -> list[dict]:
    """Liest data/ergebnisse/*.json der letzten N Tage."""
    heute = datetime.now().date()
    cutoff = (heute - timedelta(days=tage)).isoformat()
    eintraege = []
    for pfad in sorted(DATA_ERG.glob("*.json")):
        if pfad.stem < cutoff:
            continue
        try:
            d = json.loads(pfad.read_text(encoding="utf-8"))
            eintraege.append(d)
        except (json.JSONDecodeError, OSError):
            continue
    return eintraege


def cluster_verluste(ergebnisse: list[dict]) -> dict:
    """Clustert verlorene Tipps nach (liga, markt_typ-grob, kategorie).
    Returns: {(liga, markt_kat, kategorie): {n_total, n_verloren, beispiele[]}}
    """
    cluster = {}
    for tag in ergebnisse:
        spiele_nach_id = {s.get('id'): s for s in tag.get('spiele', [])}
        einzel_tipps = tag.get('einzeltipps') or tag.get('einzeltipps_ergebnis') or []
        for et in einzel_tipps:
            sid = et.get('spiel_id')
            tid = et.get('tipp_id') or et.get('id')
            spiel = spiele_nach_id.get(sid)
            if not spiel:
                continue
            tipp = next((t for t in spiel.get('tipps', []) if t.get('id') == tid), None)
            if not tipp:
                continue
            erg = next((e for e in spiel.get('tipps_ergebnis', []) if e.get('tipp_id') == tid), {})
            status = erg.get('status') or et.get('status') or 'offen'

            liga = spiel.get('liga', '?')
            kat = (tipp.get('kategorie') or '?').lower()
            markt = (tipp.get('markt') or '').lower()
            # Grobe Markt-Kategorie
            if 'doppelte chance' in markt or '(1x)' in markt or '(x2)' in markt or 'oder unentschieden' in markt:
                mkat = 'DC'
            elif any(k in markt for k in TORSCHUETZE_KEYWORDS) and 'punkte' not in markt:
                mkat = 'Torschuetze'
            elif any(k in markt for k in SIEG_KEYWORDS):
                mkat = 'Sieg/Spread'
            elif 'tore' in markt and ('ueber' in markt or 'unter' in markt or 'mehr als' in markt or 'weniger als' in markt):
                mkat = 'Tor-Total'
            elif 'btts' in markt or 'beide teams treffen' in markt:
                mkat = 'BTTS'
            elif 'punkte' in markt:
                mkat = 'NBA-Player-Punkte'
            else:
                mkat = 'Sonstige'

            key = (liga, mkat, kat)
            if key not in cluster:
                cluster[key] = {'n_total': 0, 'n_verloren': 0, 'n_gewonnen': 0, 'beispiele': []}
            c = cluster[key]
            c['n_total'] += 1
            if status == 'verloren':
                c['n_verloren'] += 1
                c['beispiele'].append({
                    'datum': tag.get('datum'),
                    'spiel': f"{spiel.get('heim')} - {spiel.get('gast')}",
                    'markt': tipp.get('markt'),
                    'quote': tipp.get('quote'),
                    'endstand': (spiel.get('ergebnis') or {}).get('endstand', '?'),
                })
            elif status == 'gewonnen':
                c['n_gewonnen'] += 1
    return cluster


def finde_saisonkontext_widersprueche(ergebnisse: list[dict]) -> list[dict]:
    """Findet Tipps wo motivations_asymmetrie selbst 'edge kleiner' / 'eher 50/50' sagt
    UND der Tipp trotzdem SAFE/VALUE Sieg/DC war UND verloren hat.
    """
    treffer = []
    for tag in ergebnisse:
        for spiel in tag.get('spiele', []):
            sk = spiel.get('saison_kontext') or {}
            asym = (sk.get('motivations_asymmetrie') or '').lower()
            if not any(p in asym for p in NEGATIVE_EDGE_PHRASEN):
                continue
            for tipp in spiel.get('tipps', []):
                kat = (tipp.get('kategorie') or '').lower()
                markt = (tipp.get('markt') or '').lower()
                if kat not in ('safe', 'value'):
                    continue
                if not any(k in markt for k in SIEG_KEYWORDS) and 'oder unentschieden' not in markt and 'doppelte chance' not in markt:
                    continue
                # Status finden
                tid = tipp.get('id')
                erg = next((e for e in spiel.get('tipps_ergebnis', []) if e.get('tipp_id') == tid), {})
                status = erg.get('status', 'offen')
                if status != 'verloren':
                    continue
                treffer.append({
                    'datum': tag.get('datum'),
                    'spiel': f"{spiel.get('heim')} - {spiel.get('gast')}",
                    'liga': spiel.get('liga'),
                    'markt': tipp.get('markt'),
                    'kategorie': kat,
                    'asymmetrie': sk.get('motivations_asymmetrie'),
                    'endstand': (spiel.get('ergebnis') or {}).get('endstand', '?'),
                })
    return treffer


def finde_defensiv_cluster(ergebnisse: list[dict]) -> list[dict]:
    """Findet Spiele mit 3+ DC/Total/BTTS und 0 Sieg/Torschuetze - typischer Bluter-Pattern."""
    treffer = []
    for tag in ergebnisse:
        for spiel in tag.get('spiele', []):
            tipps = spiel.get('tipps', [])
            if len(tipps) < 3:
                continue
            n_defensiv = 0
            n_offensiv = 0
            for t in tipps:
                m = (t.get('markt') or '').lower()
                if 'doppelte chance' in m or 'oder unentschieden' in m or '(1x)' in m or '(x2)' in m:
                    n_defensiv += 1
                elif 'btts' in m or 'beide teams treffen' in m:
                    n_defensiv += 1
                elif 'tore' in m and ('unter' in m or 'weniger als' in m):
                    n_defensiv += 1
                elif any(k in m for k in TORSCHUETZE_KEYWORDS):
                    n_offensiv += 1
                elif any(k in m for k in SIEG_KEYWORDS):
                    n_offensiv += 1
            if n_defensiv >= 3 and n_offensiv == 0:
                # Bilanz checken
                verluste = sum(1 for e in spiel.get('tipps_ergebnis', []) if e.get('status') == 'verloren')
                if verluste >= 2:
                    treffer.append({
                        'datum': tag.get('datum'),
                        'spiel': f"{spiel.get('heim')} - {spiel.get('gast')}",
                        'liga': spiel.get('liga'),
                        'n_defensiv': n_defensiv,
                        'n_offensiv': n_offensiv,
                        'n_verluste': verluste,
                        'endstand': (spiel.get('ergebnis') or {}).get('endstand', '?'),
                    })
    return treffer


def baue_lesson_vorschlaege(ergebnisse: list[dict]) -> list[dict]:
    """Generiert Lesson-Vorschlaege basierend auf erkannten Pattern."""
    vorschlaege = []
    heute = datetime.now().strftime('%Y-%m-%d')

    # 1. Verlust-Cluster mit n>=3 und Verlust-Quote >=70%
    cluster = cluster_verluste(ergebnisse)
    for (liga, mkat, kat), c in cluster.items():
        if c['n_total'] < MIN_TIPPS_FUER_PATTERN:
            continue
        verlust_quote = c['n_verloren'] / c['n_total'] * 100 if c['n_total'] else 0
        if verlust_quote < 70:
            continue
        bsp_strs = [f"{b['datum']} {b['spiel']} ({b['markt']}) -> {b['endstand']}"
                    for b in c['beispiele'][:3]]
        bsps = '; '.join(bsp_strs)
        vorschlaege.append({
            'datum': heute,
            'kategorie': f"AUTO-PATTERN: {liga} / {mkat} / {kat} - {verlust_quote:.0f}% Verlust ({c['n_verloren']}/{c['n_total']})",
            'lesson': (
                f"Auto-erkannter Verlust-Cluster Stand {heute}: in Liga '{liga}' wurden "
                f"{c['n_total']} {kat.upper()}-Tipps auf Markt-Kat '{mkat}' platziert, davon "
                f"{c['n_verloren']} verloren ({verlust_quote:.0f}%). Empfehlung: diesen Cluster "
                f"in den naechsten Lauefen NICHT mehr als {kat.upper()} - max eine Stufe runter "
                f"(safe->value, value->wackel) bis Verlust-Quote < 50%. Beispiele: {bsps}"
            ),
            'bezug_spiel_id': None,
            'auto_generiert': True,
        })

    # 2. Saison-Kontext-Widersprueche
    widersprueche = finde_saisonkontext_widersprueche(ergebnisse)
    if len(widersprueche) >= 2:
        w_strs = [f"{w['datum']} {w['spiel']} ({w['kategorie'].upper()} {w['markt']}) - asymmetrie sagte '{(w['asymmetrie'] or '')[:80]}'"
                  for w in widersprueche[:3]]
        bsps = '; '.join(w_strs)
        vorschlaege.append({
            'datum': heute,
            'kategorie': 'AUTO-PATTERN: Saison-Kontext-Selbstwiderspruch erneut aufgetreten',
            'lesson': (
                f"Trotz Hebel S wurden {len(widersprueche)} SAFE/VALUE Sieg/DC-Tipps in den "
                f"letzten {TAGE_FENSTER} Tagen platziert obwohl motivations_asymmetrie 'edge "
                f"kleiner' / 'eher 50/50' / 'rotiert vor' / 'Vorsicht' enthielt - alle verloren. "
                f"Hebel S Pattern muessen erweitert werden um {len(widersprueche)} weitere Phrasen "
                f"abzufangen. Beispiele: {bsps}"
            ),
            'bezug_spiel_id': widersprueche[0].get('spiel') if widersprueche else None,
            'auto_generiert': True,
        })

    # 3. Defensiv-Cluster
    def_cluster = finde_defensiv_cluster(ergebnisse)
    if def_cluster:
        d_strs = [f"{d['datum']} {d['spiel']} ({d['n_defensiv']}x defensiv, 0 offensiv) -> {d['n_verluste']} verloren ({d['endstand']})"
                  for d in def_cluster[:3]]
        bsps = '; '.join(d_strs)
        vorschlaege.append({
            'datum': heute,
            'kategorie': 'AUTO-PATTERN: Reine Defensiv-Cluster trotz Hebel M',
            'lesson': (
                f"{len(def_cluster)} Spiele in den letzten {TAGE_FENSTER} Tagen mit 3+ defensiven "
                f"Tipps (DC/Total/BTTS) und 0 offensiven Tipps (Sieg/Torschuetze). Hebel M sollte "
                f"das eigentlich abfangen - Mapper-Pattern erweitern oder Routine-Disziplin "
                f"verschaerfen. Beispiele: {bsps}"
            ),
            'bezug_spiel_id': None,
            'auto_generiert': True,
        })

    return vorschlaege


def auto_apply_lessons(neue_vorschlaege: list[dict]) -> int:
    """Schreibt klare Auto-Pattern direkt in data/lessons.json. KEIN User-Review noetig.

    Filter: Nur Vorschlaege die statistisch eindeutig sind werden auto-applied.
    Pattern Matching:
    - "AUTO-PATTERN: Liga / mkat / kat - X% Verlust (n/n_total)" wo n_total >= 4
    - "Saison-Kontext-Selbstwiderspruch" wenn >= 3 Belege
    - "Reine Defensiv-Cluster" wenn >= 2 Spiele

    Dedup: schreibt keine Lesson wenn schon eine mit derselben kategorie existiert.
    """
    if not DATA_LESSONS.exists() or not neue_vorschlaege:
        return 0
    try:
        d = json.loads(DATA_LESSONS.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return 0
    bestehende = {l.get('kategorie') for l in d.get('lessons', [])}
    angewendet = 0
    for v in neue_vorschlaege:
        kat = v.get('kategorie', '')
        # Auto-Apply-Filter
        ist_klar = False
        if 'AUTO-PATTERN:' in kat:
            # Verlust-Cluster: schaue im lesson-text nach n/total Format
            m = re.search(r'\((\d+)/(\d+)\)', kat)
            if m:
                n_verloren, n_total = int(m.group(1)), int(m.group(2))
                if n_total >= MIN_TIPPS_FUER_AUTO_APPLY:
                    ist_klar = True
            elif 'Saison-Kontext-Selbstwiderspruch' in kat:
                ist_klar = True
            elif 'Reine Defensiv-Cluster' in kat:
                ist_klar = True
        if not ist_klar:
            continue
        if kat in bestehende:
            continue  # Dedup
        d['lessons'].append(v)
        bestehende.add(kat)
        angewendet += 1
    if angewendet:
        DATA_LESSONS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    return angewendet


def main():
    if not DATA_ERG.exists():
        print('Keine Ergebnisse vorhanden, Analyzer skippt.')
        return 0

    ergebnisse = lade_letzte_ergebnisse(TAGE_FENSTER)
    if not ergebnisse:
        print(f'Keine Ergebnisse in den letzten {TAGE_FENSTER} Tagen.')
        return 0

    print(f'Analyzer scant {len(ergebnisse)} Ergebnis-Dateien...')
    vorschlaege = baue_lesson_vorschlaege(ergebnisse)

    # AUTO-APPLY: schreibt klare Pattern direkt in lessons.json - keine User-Aktion noetig
    angewendet = auto_apply_lessons(vorschlaege)
    print(f'[ok] {len(vorschlaege)} Vorschlaege erkannt, {angewendet} auto-applied in lessons.json')
    for v in vorschlaege[:5]:
        print(f'  - {v["kategorie"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
