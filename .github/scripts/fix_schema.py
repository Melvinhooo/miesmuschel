#!/usr/bin/env python3
"""Schema-Mapper: konvertiert Routine-Output in app.js-Format.

Routine schreibt manchmal eigene Feldnamen. Dieser Mapper bringt sie ins
strikte Format das assets/app.js erwartet.
"""
import json, glob, sys, os
from pathlib import Path

# Field-Mappings: alternative Namen -> kanonische Namen
TIPP_RENAMES = {
    'label': 'kategorie',
    'einsatz_empfehlung_kasse_prozent': 'empfohlener_einsatz_prozent',
    'einsatz_prozent': 'empfohlener_einsatz_prozent',
    'einsatz': 'empfohlener_einsatz_prozent',
}
KOMBI_RENAMES = {
    'label': 'kategorie',
    'stufe': 'kategorie',
    'tatsaechliche_quote': 'gesamtquote',
    'ziel_quote': None,  # entfernen, redundant
    'einsatz_empfehlung_kasse_prozent': 'empfohlener_einsatz_prozent',
    'einsatz_prozent': 'empfohlener_einsatz_prozent',
    'rechen_check': 'rechnung',
}
BEIN_RENAMES = {
    'auswahl': 'markt',
    'spiel': 'spiel_titel',  # nur Titel, falls keine ID; app.js nutzt spiel_id
}
EINZEL_RENAMES = {
    'label': 'kategorie',
    'einsatz_empfehlung_kasse_prozent': 'empfohlener_einsatz_prozent',
    'einsatz_prozent': 'empfohlener_einsatz_prozent',
}

# Kategorie-Normalisierung
KAT_MAP = {
    'safe': 'safe', 'sicher': 'safe',
    'value': 'value', 'wert': 'value',
    'wackel': 'wackel', 'risiko-mittel': 'wackel', 'mittel': 'wackel',
    'risk': 'risk', 'risiko': 'risk',
    'moonshot': 'moonshot', 'lottery': 'moonshot', 'lotterie': 'moonshot',
}


def remap(d, mapping):
    """Renamed Felder im dict in-place."""
    for old, new in mapping.items():
        if old in d:
            val = d.pop(old)
            if new is not None and new not in d:
                d[new] = val


def normalize_kategorie(d):
    if 'kategorie' in d and isinstance(d['kategorie'], str):
        k = d['kategorie'].strip().lower()
        d['kategorie'] = KAT_MAP.get(k, k)


# Saison-Kontext-Pflichtfelder (Recherche-Hartregel).
# Routine MUSS pro Spiel saison_kontext{} ausfuellen, sonst werden Tipps gedroppt.
# Hintergrund: Routine erfindet sich oft Kontext zusammen (Bayern-CL-Rotation ignoriert,
# Leipzig-Conference erfunden, Freiburg-EL uebersehen). Mechanische Erzwingung.
PFLICHT_KONTEXT_FELDER = [
    'parallel_heim',
    'parallel_gast',
    'saisonziel_heim',
    'saisonziel_gast',
    'motivations_asymmetrie',
    'recovery_heim',
    'recovery_gast',
]
WETTBEWERB_PATTERNS = ('cl', 'champions', 'el', 'europa', 'conference', 'pokal',
                       'fa cup', 'coppa', 'copa', 'copa del rey')
# Hosts die als Verband-/Liga-Quelle akzeptiert werden bei Wettbewerbs-Behauptungen.
# Verbaende (UEFA/FIFA/DFB) + offizielle Liga-Sites + kicker/sofascore/espn als pragmatische
# Cross-League-Quellen + grosse Klub-Sites.
QUELLEN_HOSTS_VERBAND = (
    'uefa.com', 'dfb.de', 'fifa.com',
    'premierleague.com', 'bundesliga.com', 'laliga.com',
    'legaseriea.it', 'lega-serie-a', 'ligue1.com',
    'kicker.de', 'sofascore.com', 'flashscore', 'espn.com',
    'transfermarkt', 'liverpoolfc.com', 'cpfc.co.uk', 'manutd.com',
)


def validate_saison_kontext(d):
    """Pflichtfeld-Check fuer saison_kontext pro Spiel.

    Modi via Env MIESMUSCHEL_KONTEXT_MODE:
      "hard" (Default) - FAIL droppt tipps[], WARN_QUELLE downgraded SAFE/VALUE auf wackel.
                         Recherche ist nicht optional, Halluzinationen werden ausgefiltert.
      "soft"             - nur kontext_check_status + Logging, KEIN Tipps-Drop, KEIN Downgrade.
                         Nur fuer Bootstrap/Migration einer Datei genutzt.
    """
    mode = os.environ.get('MIESMUSCHEL_KONTEXT_MODE', 'hard').strip().lower()
    hart = (mode == 'hard')

    for spiel in d.get('spiele', []):
        kontext = spiel.get('saison_kontext') or {}
        fehler = []
        for f in PFLICHT_KONTEXT_FELDER:
            v = kontext.get(f)
            if not isinstance(v, str) or not v.strip():
                fehler.append(f)
        quellen = kontext.get('quellen') or []
        gueltige_quellen = [q for q in quellen if isinstance(q, str) and q.strip()] if isinstance(quellen, list) else []
        if not gueltige_quellen:
            fehler.append('quellen[]')

        if fehler:
            spiel['kontext_check_status'] = 'FAIL'
            spiel['kontext_check_fehler'] = fehler
            n_tipps = len(spiel.get('tipps', []))
            if hart:
                spiel['tipps'] = []
                print(f"  saison_kontext FAIL '{spiel.get('id', '?')}': fehlt {fehler} -> {n_tipps} Tipps gedroppt")
            else:
                print(f"  saison_kontext FAIL (soft) '{spiel.get('id', '?')}': fehlt {fehler} -> {n_tipps} Tipps WUERDEN gedroppt im hard-mode")
            continue

        # Quellen-Check fuer parallele Wettbewerbe (Verband-URL Pflicht wenn CL/EL/Pokal genannt).
        nennt_wettbewerb = False
        for f in ('parallel_heim', 'parallel_gast'):
            v = (kontext.get(f) or '').lower().strip()
            if v in ('', 'keine', 'nein', '-', 'keine doppelbelastung'):
                continue
            if any(p in v for p in WETTBEWERB_PATTERNS):
                nennt_wettbewerb = True
                break

        if nennt_wettbewerb:
            quellen_str = ' '.join(q.lower() for q in gueltige_quellen)
            hat_verband_quelle = any(h in quellen_str for h in QUELLEN_HOSTS_VERBAND)
            if not hat_verband_quelle:
                spiel['kontext_check_status'] = 'WARN_QUELLE'
                if hart:
                    downgraded = 0
                    for tipp in spiel.get('tipps', []):
                        kat = (tipp.get('kategorie') or '').lower()
                        if kat in ('safe', 'value'):
                            tipp['kategorie'] = 'wackel'
                            downgraded += 1
                    if downgraded:
                        print(f"  saison_kontext WARN_QUELLE '{spiel.get('id', '?')}': "
                              f"Wettbewerb genannt aber keine Verband-URL in quellen[] -> "
                              f"{downgraded} SAFE/VALUE-Tipps auf wackel degradiert")
                else:
                    print(f"  saison_kontext WARN_QUELLE (soft) '{spiel.get('id', '?')}': "
                          f"Wettbewerb genannt aber keine Verband-URL in quellen[] -> "
                          f"WUERDE SAFE/VALUE auf wackel degradieren im hard-mode")
                continue

        spiel['kontext_check_status'] = 'OK'
        spiel.pop('kontext_check_fehler', None)


def fix(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)

    # Spiele: tipps[] fixen
    for spiel in d.get('spiele', []):
        for tipp in spiel.get('tipps', []):
            remap(tipp, TIPP_RENAMES)
            normalize_kategorie(tipp)
            # tipp_id -> id normalisieren (Routine schreibt mal so, mal so).
            # Ohne diese Normalisierung droppt der Mapper spaeter alle einzeltipps/kombis,
            # weil valid_refs mit `id` matched, aber Tipps nur `tipp_id` haben.
            if 'id' not in tipp and 'tipp_id' in tipp:
                tipp['id'] = tipp.pop('tipp_id')
            # markt+auswahl kombinieren (Routine schreibt oft markt=Typ, auswahl=Pick)
            if tipp.get('auswahl'):
                # Wenn auswahl verständlicher als markt allein → ersetze
                tipp['markt'] = tipp['auswahl']
                tipp.pop('auswahl', None)
            # Markt-Typ-Praefixe in eckigen Klammern entfernen die Routine manchmal anhaengt
            for prefix in ['Spieler-Punkte (NUR für Risiko/Moonshot, nicht Einzeltipps)',
                          'Spieler-Punkte (RISIKO/MOONSHOT-Optionsbein, nicht Einzeltipp)',
                          'Tipp-Spieler Punkte (RISIKO/MOONSHOT)']:
                if tipp.get('markt') == prefix:
                    tipp['markt'] = 'Spieler-Punkte (Risiko/Moonshot)'
            # faire_quote default falls fehlt
            if 'faire_quote' not in tipp or tipp['faire_quote'] is None:
                if tipp.get('quote') and tipp.get('edge_prozent'):
                    # faire_quote = quote / (1 + edge/100)
                    try:
                        tipp['faire_quote'] = round(float(tipp['quote']) / (1 + float(tipp['edge_prozent'])/100), 2)
                    except (ValueError, ZeroDivisionError):
                        tipp['faire_quote'] = tipp['quote']
                else:
                    tipp['faire_quote'] = tipp.get('quote', 0)
            # empfohlener_einsatz_prozent default
            if 'empfohlener_einsatz_prozent' not in tipp:
                kat = tipp.get('kategorie', '')
                tipp['empfohlener_einsatz_prozent'] = {'safe': 1.5, 'value': 1.0, 'wackel': 0.5}.get(kat, 0.5)

    # Einzeltipps fixen
    for et in d.get('einzeltipps', []):
        remap(et, EINZEL_RENAMES)
        normalize_kategorie(et)
        # markt+auswahl mergen wie bei tipps[]
        if et.get('auswahl'):
            et['markt'] = et['auswahl']
            et.pop('auswahl', None)
        if 'empfohlener_einsatz_prozent' not in et:
            kat = et.get('kategorie', '')
            et['empfohlener_einsatz_prozent'] = {'safe': 1.5, 'value': 1.0, 'wackel': 0.5}.get(kat, 0.5)

    # Kombis fixen
    for k in d.get('kombis', []):
        remap(k, KOMBI_RENAMES)
        normalize_kategorie(k)
        if 'empfohlener_einsatz_prozent' not in k:
            kat = k.get('kategorie', '')
            k['empfohlener_einsatz_prozent'] = {'safe': 1.5, 'value': 0.8, 'risk': 0.25, 'moonshot': 0.1}.get(kat, 0.5)
        # Beine
        for bein in k.get('beine', []):
            remap(bein, BEIN_RENAMES)
            # auswahl in markt mergen wenn vorhanden
            if bein.get('auswahl') and not bein.get('markt'):
                bein['markt'] = bein['auswahl']
                bein.pop('auswahl', None)
            # Match-Info ins markt-Feld einbauen damit app.js es zeigt (split via ':')
            # app.js zeigt vor ":" als Match-Header, danach als Pick
            if bein.get('spiel_titel'):
                import re
                titel = bein['spiel_titel']
                # Klammer-Suffixe wie "(CL HF Hinspiel)" / "(NBA)" entfernen
                clean_titel = re.sub(r'\s*\([^)]*\)\s*$', '', titel).strip()
                cur_markt = bein.get('markt', '')
                # Nur praependen wenn Markt nicht schon mit Titel anfaengt
                if cur_markt and not cur_markt.startswith(clean_titel):
                    bein['markt'] = f"{clean_titel}: {cur_markt}"

    # Schlechte Markt-Typen droppen (Lottery, exotisch, doppelt)
    # Routine entscheidet selbst wie viele Tipps - nur Muell rauswerfen
    DROP_PATTERNS = [
        'exakt',                   # "Anzahl Tore exakt" - Lottery
        'spielausgang hz',         # HZ/ES-Kombi - sehr unzuverlaessig
        'hz/es',
        'halbzeit/endstand',
        '100+ punkte',             # Quasi sicher bei NBA, kein Edge
        'genaues ergebnis',        # Lottery
        'erste karte',             # Karten verboten in DE eh
        'eckball',                 # verboten
    ]
    for spiel in d.get('spiele', []):
        kept = []
        for tipp in spiel.get('tipps', []):
            markt = (tipp.get('markt') or '').lower()
            if any(p in markt for p in DROP_PATTERNS):
                continue
            kept.append(tipp)
        spiel['tipps'] = kept

    # Saison-Kontext-Pflichtcheck: Spiele ohne saison_kontext kriegen ihre Tipps gedroppt.
    # Spiele mit unzureichender Quellen-Belegung werden auf wackel degradiert.
    # Muss VOR dem Hard-Cap laufen, damit die einzeltipps/kombis-Bereinigung weiter unten
    # die referenzierten Tipps nicht mehr findet und sie automatisch droppt.
    validate_saison_kontext(d)

    # Hard-Cap: max 5 Tipps pro Spiel, sortiert nach Kategorie-Prioritaet + Edge.
    # SAFE > VALUE > WACKEL > RISIKO > MOONSHOT, innerhalb gleicher Kategorie nach edge_prozent absteigend.
    KAT_PRIORITY = {'safe': 0, 'value': 1, 'wackel': 2, 'risk': 3, 'moonshot': 4}
    def _score(t):
        kat = (t.get('kategorie') or 'wackel').lower()
        p = KAT_PRIORITY.get(kat, 5)
        try:
            edge = float(t.get('edge_prozent') or 0)
        except (ValueError, TypeError):
            edge = 0
        return (p, -edge)
    MAX_TIPPS_PRO_SPIEL = 5
    for spiel in d.get('spiele', []):
        tipps = spiel.get('tipps', [])
        if len(tipps) > MAX_TIPPS_PRO_SPIEL:
            spiel['tipps'] = sorted(tipps, key=_score)[:MAX_TIPPS_PRO_SPIEL]

    # Konsistenz: einzeltipps[] und kombis[] bereinigen, falls ein Tipp gecappt wurde.
    valid_refs = set()
    for spiel in d.get('spiele', []):
        sid = spiel.get('id')
        for t in spiel.get('tipps', []):
            tid = t.get('id')
            if sid and tid:
                valid_refs.add((sid, tid))

    et_before = len(d.get('einzeltipps', []))
    d['einzeltipps'] = [
        e for e in d.get('einzeltipps', [])
        if not e.get('tipp_id') or (e.get('spiel_id'), e.get('tipp_id')) in valid_refs
    ]
    for i, e in enumerate(d.get('einzeltipps', []), 1):
        e['rang'] = i
    if et_before != len(d.get('einzeltipps', [])):
        print(f"  einzeltipps Cap-Cleanup: {et_before} -> {len(d['einzeltipps'])}")

    kept_kombis = []
    for k in d.get('kombis', []):
        beine = k.get('beine', [])
        # Nur Beine mit eindeutigem tipp_id pruefen; ohne tipp_id (nur Markt-String) drinlassen
        all_valid = all(
            (b.get('spiel_id'), b.get('tipp_id')) in valid_refs
            for b in beine if b.get('tipp_id')
        )
        if all_valid:
            kept_kombis.append(k)
        else:
            print(f"  Kombi gedroppt nach Cap: {k.get('name', k.get('id', '?'))}")
    d['kombis'] = kept_kombis

    # Diversifikations-Regel: max 1 Bein pro Spiel pro Kombi.
    # Lehre vom 28.04.2026 (Celtics-Embiid): wenn ein Spiel-Bein in mehreren Kombis steckt,
    # toetet ein einzelner Spielausgang die ganze Kombi-Zeile. In einer SINGLE Kombi
    # mehrere Beine vom selben Spiel zu haben ist die gleiche Falle in extrem.
    # Wir behalten das stark-priorisierte Bein (SAFE > VALUE > WACKEL) pro Spiel.
    BEIN_KAT_PRIORITY = {'safe': 0, 'value': 1, 'wackel': 2, 'risk': 3, 'moonshot': 4}
    def _bein_score(b):
        # Suche kategorie ueber tipp_id-Lookup im Spiele-Tipps-Array
        sid, tid = b.get('spiel_id'), b.get('tipp_id')
        for spiel in d.get('spiele', []):
            if spiel.get('id') == sid:
                for t in spiel.get('tipps', []):
                    if t.get('id') == tid:
                        kat = (t.get('kategorie') or 'wackel').lower()
                        try:
                            edge = float(t.get('edge_prozent') or 0)
                        except (ValueError, TypeError):
                            edge = 0
                        return (BEIN_KAT_PRIORITY.get(kat, 5), -edge)
        return (5, 0)  # Fallback: niedrigste Prio

    for k in d.get('kombis', []):
        beine = k.get('beine', [])
        if len(beine) <= 1:
            continue
        # Gruppiere Beine pro Spiel-ID, behalte pro Spiel das beste Bein
        seen_spiele = {}
        sorted_beine = sorted(beine, key=_bein_score)
        kept_beine = []
        for b in sorted_beine:
            sid = b.get('spiel_id')
            if sid and sid in seen_spiele:
                continue  # zweites Bein vom selben Spiel -> droppen
            if sid:
                seen_spiele[sid] = True
            kept_beine.append(b)
        if len(kept_beine) < len(beine):
            # Reihenfolge wieder herstellen: nach urspruenglicher Position
            orig_idx = {id(b): i for i, b in enumerate(beine)}
            kept_beine.sort(key=lambda b: orig_idx.get(id(b), 999))
            print(f"  Kombi '{k.get('name', k.get('id', '?'))}': Diversifikation, "
                  f"{len(beine)} -> {len(kept_beine)} Beine (1 pro Spiel)")
            k['beine'] = kept_beine
            # Gesamtquote neu berechnen
            try:
                neue_quote = 1.0
                for b in kept_beine:
                    neue_quote *= float(b.get('quote') or 1.0)
                k['gesamtquote'] = round(neue_quote, 2)
                # Rechnung aktualisieren wenn vorhanden
                quoten_str = ' × '.join(f"{float(b.get('quote') or 1.0):.2f}" for b in kept_beine)
                k['rechnung'] = f"{quoten_str} = {k['gesamtquote']}"
            except (ValueError, TypeError):
                pass

    # Layer-2-Diversifikations-Check: zaehle wie oft jedes Spiel in Sieg-Beinen vorkommt
    # ueber alle Kombis. Wenn ein Spiel-Sieg-Outcome in >2 Kombis steckt, WARN
    # (nicht hartcoded weil semantisch komplex - Routine soll selbst loesen).
    sieg_marker = ('sieg', 'moneyline', 'spread', 'handicap', '1x2', 'doppelte chance')
    spiel_in_sieg_kombis = {}
    for k in d.get('kombis', []):
        spiele_in_kombi_sieg = set()
        for b in k.get('beine', []):
            sid = b.get('spiel_id')
            if not sid:
                continue
            markt = (b.get('markt') or '').lower()
            if any(m in markt for m in sieg_marker):
                spiele_in_kombi_sieg.add(sid)
        for sid in spiele_in_kombi_sieg:
            spiel_in_sieg_kombis[sid] = spiel_in_sieg_kombis.get(sid, 0) + 1
    for sid, n in spiel_in_sieg_kombis.items():
        if n > 2:
            print(f"  WARN Layer-2: Spiel-Sieg-Outcome '{sid}' in {n} Kombis - "
                  f"Diversifikations-Risiko (1 Spiel-Verlust killt {n} Kombis). "
                  f"Routine soll bei naechstem Lauf andere Markttypen waehlen.")

    # _test_trigger Cleanup
    d.pop('_test_trigger', None)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"Schema-Fix OK: {path}")


PFADE = [
    'data/tipps/*.json',
    'data/tipps_wochenende/*.json',
    'data/tipps_woche/*.json',
]


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = []
        for pattern in PFADE:
            files.extend(sorted(glob.glob(pattern)))
    for f in files:
        fix(f)


if __name__ == '__main__':
    main()
