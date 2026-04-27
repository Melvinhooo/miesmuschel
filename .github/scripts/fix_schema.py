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


def fix(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)

    # Spiele: tipps[] fixen
    for spiel in d.get('spiele', []):
        for tipp in spiel.get('tipps', []):
            remap(tipp, TIPP_RENAMES)
            normalize_kategorie(tipp)
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
            # spiel_id aus spiel_titel ableiten (matching auf heim/gast in spiele[])
            if not bein.get('spiel_id') and bein.get('spiel_titel'):
                titel = bein['spiel_titel'].lower()
                for spiel in d.get('spiele', []):
                    h = (spiel.get('heim') or '').lower()
                    g = (spiel.get('gast') or '').lower()
                    # Heuristik: heim und gast Substring im Titel
                    if h and g and h in titel and g in titel:
                        bein['spiel_id'] = spiel['id']
                        break
                    # Schwaechere Heuristik: nur kurzformen
                    if h and g:
                        h_short = h.split()[0] if ' ' in h else h
                        g_short = g.split()[0] if ' ' in g else g
                        if h_short in titel and g_short in titel:
                            bein['spiel_id'] = spiel['id']
                            break

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

    # _test_trigger Cleanup
    d.pop('_test_trigger', None)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"Schema-Fix OK: {path}")


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = sorted(glob.glob('data/tipps/*.json'))
    for f in files:
        fix(f)


if __name__ == '__main__':
    main()
