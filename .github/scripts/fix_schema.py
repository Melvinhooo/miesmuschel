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
    # Routine schreibt manchmal quote_bet365, app.js liest aber t.quote -> sonst 0.00 Anzeige
    'quote_bet365': 'quote',
    'bet365_quote': 'quote',
}
EINZEL_QUOTE_RENAMES = {'quote_bet365': 'quote', 'bet365_quote': 'quote'}
KOMBI_RENAMES = {
    'label': 'kategorie',
    'stufe': 'kategorie',
    'tatsaechliche_quote': 'gesamtquote',
    'gesamt_quote': 'gesamtquote',  # Underscore-Variante (Routine schreibt mal so, mal so)
    'ziel_quote': None,  # entfernen, redundant
    'einsatz_empfehlung_kasse_prozent': 'empfohlener_einsatz_prozent',
    'einsatz_prozent': 'empfohlener_einsatz_prozent',
    'rechen_check': 'rechnung',
}
BEIN_RENAMES = {
    'auswahl': 'markt',
    'spiel': 'spiel_titel',  # nur Titel, falls keine ID; app.js nutzt spiel_id
    'quote_bet365': 'quote',
    'bet365_quote': 'quote',
}
EINZEL_RENAMES = {
    'label': 'kategorie',
    'einsatz_empfehlung_kasse_prozent': 'empfohlener_einsatz_prozent',
    'einsatz_prozent': 'empfohlener_einsatz_prozent',
    'quote_bet365': 'quote',
    'bet365_quote': 'quote',
}
BEIN_QUOTE_RENAMES = {'quote_bet365': 'quote', 'bet365_quote': 'quote'}

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
# Wettbewerb-Patterns: nur LANGE/EINDEUTIGE Tokens. Frueher waren 'cl' und 'el'
# als Substring-Match drin - das traf in deutschen Texten auf 'Spiel', 'Mehl' etc.
# (08.05.: false positive im NBA-Spiel weil 'el' in 'Spiel' matched). Jetzt nur
# eindeutige Multi-Char-Tokens, plus die kurzen Tokens nur als Bindestrich-Variante
# (cl-spiel, el-rueckspiel, cl-quali etc).
WETTBEWERB_PATTERNS = ('champions league', 'champions-league', 'cl-spiel', 'cl-quali',
                       'cl-doppelbelastung', 'cl-halbfinale', 'cl-achtelfinale',
                       'europa league', 'europa-league', 'el-spiel', 'el-quali',
                       'el-doppelbelastung', 'el-halbfinale', 'el-rueckspiel', 'el-hinspiel',
                       'conference league', 'conference-league', 'conference-quali',
                       'dfb-pokal', 'pokal-halbfinale', 'pokal-finale', 'pokal-spiel',
                       'fa cup', 'coppa italia', 'copa del rey', 'coupe de france')
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


def lade_markt_bluter():
    """Liest data/markt_bluter.json (auto-generiert von statistik_berechnen.py).
    Returns: liste der Markt-Typ-Strings (z.B. ['Beide Teams treffen JA', 'Spieler-Punkte Unter (NBA)'])
    Bei Fehler: leere Liste (kein Filter aktiv).
    """
    pfad = os.path.join('data', 'markt_bluter.json')
    if not os.path.exists(pfad):
        return []
    try:
        with open(pfad, encoding='utf-8') as f:
            d = json.load(f)
        return [m.get('markt') for m in d.get('maerkte', []) if m.get('markt')]
    except (json.JSONDecodeError, OSError, KeyError):
        return []


def lade_beobachtungs_ligen():
    """Liest data/beobachtungs_ligen.json (auto-generiert von statistik_berechnen.py).
    Returns: liste der Liga-Strings die in Beobachtungs-Status sind.
    Bei Fehler: leere Liste.
    """
    pfad = os.path.join('data', 'beobachtungs_ligen.json')
    if not os.path.exists(pfad):
        return []
    try:
        with open(pfad, encoding='utf-8') as f:
            d = json.load(f)
        return [l.get('liga') for l in d.get('ligen', []) if l.get('liga')]
    except (json.JSONDecodeError, OSError, KeyError):
        return []


def lade_markt_goldgruben():
    """Liest data/markt_goldgruben.json (auto-generiert von statistik_berechnen.py).
    Returns: liste der Markt-Typ-Strings die in Goldgrube-Status sind.
    Bei Fehler: leere Liste.
    """
    pfad = os.path.join('data', 'markt_goldgruben.json')
    if not os.path.exists(pfad):
        return []
    try:
        with open(pfad, encoding='utf-8') as f:
            d = json.load(f)
        return [m.get('markt') for m in d.get('maerkte', []) if m.get('markt')]
    except (json.JSONDecodeError, OSError, KeyError):
        return []


def lade_liga_goldgruben():
    """Liest data/liga_goldgruben.json (auto-generiert von statistik_berechnen.py).
    Returns: dict {liga -> stat-dict mit 'tipps', 'trefferquote', 'roi_prozent', 'netto'}.
    Bei Fehler: leeres dict. Brauchen das volle Dict (nicht nur die Liga-Strings),
    weil validate_safe_confirm() unterscheiden muss zwischen "Liga in Goldgrube"
    (n>=5, ROI>0, Hitrate>=65) und "Liga zu wenig Daten" (n<5, dann SAFE bleibt).
    """
    pfad = os.path.join('data', 'liga_goldgruben.json')
    if not os.path.exists(pfad):
        return {}
    try:
        with open(pfad, encoding='utf-8') as f:
            d = json.load(f)
        return {l.get('liga'): l for l in d.get('ligen', []) if l.get('liga')}
    except (json.JSONDecodeError, OSError, KeyError):
        return {}


def lade_liga_stats():
    """Liest data/statistik.json -> nach_liga{} fuer Liga-Sample-Check.
    Returns: dict {liga -> {'tipps': n, 'trefferquote': %, 'roi_prozent': %}}.
    Bei Fehler: leeres dict. Damit kann validate_safe_confirm() unterscheiden:
    Liga existiert nicht oder n<5 -> liga_unbekannt=True -> SAFE bleibt (Datenmangel
    ist kein Strafgrund, sonst killen wir z.B. DFB-Pokal HF mit +46% ROI bei n=4).
    """
    pfad = os.path.join('data', 'statistik.json')
    if not os.path.exists(pfad):
        return {}
    try:
        with open(pfad, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('nach_liga') or {}
    except (json.JSONDecodeError, OSError, KeyError):
        return {}


# Regex-Floor: NBA Playoff Decider (G5/G6/G7) immer als Beobachtungs-Liga behandeln,
# auch wenn die Statistik sie nicht auto-erkennt (zu wenig Sample, oder Liga-String
# anders geschrieben). 04.05.: G6 = -45.6% ROI, G5 = -16.7% ROI -> klare Bluter.
# Match auf "NBA Playoffs ... G5/G6/G7" oder "NBA Playoffs ... Game 5/6/7" case-insensitive.
import re as _re_nba
NBA_DECIDER_PATTERN = _re_nba.compile(
    r'nba\s*playoffs.*\b(?:game\s*[567]|g[567])\b',
    _re_nba.IGNORECASE,
)


def validate_beobachtungs_liga(d):
    """ROI-SANIERUNG 04.05.2026: Beobachtungs-Liga-Tipps HARTCODED aus
    einzeltipps[] und Safe/Balance/Risiko-Kombis droppen. Moonshot-Kombi
    erlaubt sie als Spass-Bein ab Quote >= 5.

    Hintergrund: 04.05. Statistik zeigte 2. Bundesliga -40% ROI bei 5 Tipps
    obwohl seit 27.04. in beobachtungs_ligen.json. Routine-Prompt-Anweisung
    reicht nicht - mechanische Erzwingung noetig.
    """
    beob_ligen = set(lade_beobachtungs_ligen())
    # ROI-Sanierung Hebel B 04.05.: NBA-Playoff-Decider (G5/G6/G7) zaehlen IMMER als
    # Beobachtungs-Liga, auch ohne Auto-Erkennung. Selbst wenn der Statistik-Sample
    # zu klein ist oder der Liga-String nicht in beobachtungs_ligen.json steht.

    # Sammle spiel_ids in Beobachtungs-Ligen (Liste-Match ODER NBA-Decider-Regex)
    beob_spiel_ids = set()
    matched_ligen = set()
    for spiel in d.get('spiele', []):
        liga = spiel.get('liga', '')
        if liga in beob_ligen or NBA_DECIDER_PATTERN.search(liga):
            sid = spiel.get('id')
            if sid:
                beob_spiel_ids.add(sid)
                matched_ligen.add(liga)

    if not beob_spiel_ids:
        return

    # 1. einzeltipps[] aus Beobachtungs-Liga-Spielen droppen
    et_before = len(d.get('einzeltipps', []))
    d['einzeltipps'] = [e for e in d.get('einzeltipps', [])
                       if e.get('spiel_id') not in beob_spiel_ids]
    et_dropped = et_before - len(d['einzeltipps'])
    if et_dropped:
        # Rang neu durchnummerieren
        for i, e in enumerate(d['einzeltipps'], 1):
            e['rang'] = i
        print(f"  Beobachtungs-Liga: {et_dropped} Einzeltipps gedroppt (Spiele in {sorted(matched_ligen)})")

    # 2. Kombis: Beobachtungs-Liga-Beine droppen aus Safe/Balance/Risiko
    #    Moonshot-Kombi ueberlebt mit Beob-Beinen wenn Quote >= 5.0
    for k in d.get('kombis', []):
        kategorie = (k.get('kategorie') or '').lower()
        ist_moonshot = kategorie == 'moonshot' or 'moonshot' in (k.get('name') or '').lower()
        beine = k.get('beine', [])
        kept = []
        for b in beine:
            sid = b.get('spiel_id')
            quote = b.get('quote', 0)
            try:
                quote = float(quote)
            except (TypeError, ValueError):
                quote = 0
            if sid in beob_spiel_ids:
                if ist_moonshot and quote >= 5.0:
                    kept.append(b)  # Moonshot-Bein ab 5x erlaubt
                else:
                    print(f"  Beobachtungs-Liga: Kombi-Bein gedroppt aus '{k.get('name','?')}' "
                          f"(spiel_id {sid}, Quote {quote})")
                    continue
            else:
                kept.append(b)
        if len(kept) < len(beine):
            k['beine'] = kept
            # Gesamtquote neu berechnen
            try:
                neue_quote = 1.0
                for b in kept:
                    neue_quote *= float(b.get('quote') or 1.0)
                k['gesamtquote'] = round(neue_quote, 2)
                k['rechnung'] = ' x '.join(f"{float(b.get('quote') or 1.0):.2f}" for b in kept) + f" = {k['gesamtquote']}"
            except (ValueError, TypeError):
                pass


def markt_typ_pattern(markt):
    """Mini-Replikat von scripts/statistik_berechnen.py:markt_typ() - nur die Aggregations-Logik
    die wir hier brauchen um einen Tipp-Markt-String auf Markt-Typ zu mappen. Sonst muessten
    wir das ganze Modul importieren - inline-Lookup ist robuster fuer Action-Umgebungen.
    """
    if not markt:
        return 'Sonstige'
    m = markt.lower()
    if 'doppelte chance' in m or ' dc ' in f' {m} ' or ' dc-' in m:
        if '(1x)' in m or ' 1x' in m: return 'Doppelte Chance 1X'
        if '(x2)' in m or ' x2' in m: return 'Doppelte Chance X2'
        if '(12)' in m: return 'Doppelte Chance 12'
        return 'Doppelte Chance'
    if 'beide teams treffen' in m or 'btts' in m:
        if ' ja' in m or '(ja)' in m: return 'Beide Teams treffen JA'
        if ' nein' in m or '(nein)' in m: return 'Beide Teams treffen NEIN'
        return 'Beide Teams treffen'
    if ('trifft' in m or 'torschuetz' in m or 'jederzeit tor' in m or 'tor (jederzeit)' in m) and 'punkte' not in m:
        if 'doppelpack' in m: return 'Torschuetzen Doppelpack'
        if 'hattrick' in m: return 'Torschuetzen Hattrick'
        if 'erster' in m: return 'Torschuetzen Erster'
        return 'Torschuetzen Jederzeit'
    if 'tore' in m or ' tor ' in f' {m} ':
        import re
        zahl = re.search(r'(\d+\.5)', m)
        zahl_str = zahl.group(1) if zahl else '?'
        if 'mehr als' in m or 'ueber' in m or 'über' in m:
            return f'Ueber {zahl_str} Tore'
        if 'weniger als' in m or 'unter' in m:
            return f'Unter {zahl_str} Tore'
    if 'punkte' in m:
        if 'mehr als' in m or 'ueber' in m or 'über' in m:
            if 'gesamt' in m or 'total' in m: return 'Total Ueber (NBA)'
            return 'Spieler-Punkte Ueber (NBA)'
        if 'weniger als' in m or 'unter' in m:
            if 'gesamt' in m or 'total' in m: return 'Total Unter (NBA)'
            return 'Spieler-Punkte Unter (NBA)'
        if 'double-double' in m: return 'Double-Double (NBA)'
        if 'triple-double' in m: return 'Triple-Double (NBA)'
    if 'spread' in m or 'handicap' in m:
        return 'Spread/Handicap'
    if 'moneyline' in m or '(ml)' in m or '(1x2)' in m or '1x2' in m or m.endswith(' sieg') or ' sieg ' in f' {m} ':
        return 'Sieg (1X2 / ML)'
    if '1.hz' in m or 'halbzeit-sieger' in m:
        return '1.HZ Sieger'
    return markt  # Fallback


def validate_markt_bluter(d):
    """Filtert Bluter-Maerkte: SAFE/VALUE-Tipps auf Markt-Typen die in data/markt_bluter.json
    gelistet sind werden auf wackel degradiert. Damit wird die Lesson-Anwendung mechanisch
    erzwungen statt in der Routine-Begruendung zu hoffen.

    Analog zu Beobachtungs-Liga (jene filtert nach liga, hier nach markt_typ).
    """
    bluter_typen = lade_markt_bluter()
    if not bluter_typen:
        return  # Kein Bluter-File oder leer - kein Filter aktiv
    bluter_set = set(bluter_typen)
    downgraded_count = 0
    for spiel in d.get('spiele', []):
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            mtyp = markt_typ_pattern(tipp.get('markt', ''))
            if mtyp in bluter_set:
                tipp['kategorie'] = 'wackel'
                tipp['_markt_bluter_downgrade'] = True
                downgraded_count += 1
    if downgraded_count:
        print(f"  markt_bluter Filter: {downgraded_count} SAFE/VALUE-Tipps auf wackel degradiert "
              f"(Markt-Typen in markt_bluter.json: {sorted(bluter_set)})")


def _sync_einzeltipp_kategorie(d, sid, tid, neue_kat):
    """Wenn ein spiele[].tipps[]-Eintrag downgegraded wurde, halte das passende
    einzeltipps[]-Element in Sync. Sonst zeigt das UI noch die alte Kategorie an
    obwohl die kanonische Quelle (spiele.tipps) bereits downgegraded ist.
    """
    for e in d.get('einzeltipps', []):
        if e.get('spiel_id') == sid and e.get('tipp_id') == tid:
            e['kategorie'] = neue_kat


def validate_nba_playoff(d):
    """ROI-SANIERUNG Hebel B 04.05.2026 (v2 differenziert): NBA-Playoff-Decider haerten.

    Bilanz Stand 04.05.: NBA Playoffs Round 1 Game 6 = -45.6% ROI bei 7 Tipps,
    Game 5 = -16.7% ROI bei 13 Tipps. Game 1-4 + Conference Finals + NBA Finals
    nicht im Bluter-Pattern - dort SAFE bleibt erlaubt.

    LEHRE 04.05. (User-Feedback): "Statt Markt-Boykott differenziert lernen."
    Frueher: alle NBA-Playoff-Tipps SAFE -> VALUE pauschal. Das war Loeschen,
    nicht Lernen. Neu: nur Decider (G5/G6/G7) trifft die Bluter-Phase, dort
    Sieg/Spread/Total/DC max WACKEL. G1-G4 + Conference Finals + NBA Finals
    sind SAFE-faehig wenn Edge da ist.

    Regel: Decider-Spiele (Game 5/6/7) - Sieg/Spread/Total/DC -> WACKEL.
    Begruendung: Closeout/Decider-Varianz extrem (Ueberraschungs-Sweeps,
    Star-Out-Lineup-Wechsel, Defensiv-Schlachten). Player-Punkte/DD/TD im
    Decider werden vom Markt-Bluter-Filter erfasst falls sie negativ
    aufgefallen sind.
    """
    decider_keywords = (
        'sieg', 'spread', 'handicap', 'moneyline', 'ml',
        'total', 'gesamt', 'ueber', 'über', 'unter',
        'doppelte chance', ' dc ', '(1x)', '(x2)',
    )
    downgrades_to_wackel = 0
    for spiel in d.get('spiele', []):
        liga = spiel.get('liga') or ''
        if 'nba playoffs' not in liga.lower():
            continue
        ist_decider = bool(NBA_DECIDER_PATTERN.search(liga))
        if not ist_decider:
            # G1-G4 oder Conference Finals oder NBA Finals - keine Auto-Filter,
            # Routine entscheidet selbst basierend auf Edge.
            continue
        sid = spiel.get('id')
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            tid = tipp.get('id')
            if kat not in ('safe', 'value'):
                continue
            markt_lower = (tipp.get('markt') or '').lower()
            if any(k in markt_lower for k in decider_keywords):
                tipp['kategorie'] = 'wackel'
                tipp['_nba_decider_downgrade'] = True
                begr = tipp.get('begruendung') or ''
                tipp['begruendung'] = (begr + ' [Auto: NBA G5+/Decider Sieg/Spread/Total - max WACKEL wegen Closeout-Varianz]').strip()
                _sync_einzeltipp_kategorie(d, sid, tid, 'wackel')
                downgrades_to_wackel += 1
    if downgrades_to_wackel:
        print(f"  NBA-Decider-Filter: {downgrades_to_wackel} Sieg/Spread/Total in Decider (G5-7) -> WACKEL")


def validate_safe_confirm(d):
    """SAFE-Confirm-Validator (entschaerft 08.05.2026 nach User-Feedback):
    SAFE-Label bleibt erhalten WENN nicht aktiv negative Signale gegen den Tipp stehen.

    Vorgaenger-Version (04.05.) war zu hart: SAFE -> VALUE wenn Liga NICHT in
    liga_goldgruben.json. Effekt: BVB / Lens / Bayern etc. nie SAFE weil ihre Liga
    nicht in der kleinen Goldgruben-Liste ist (PL/LaLiga/CL-HF/EL-HF/NBA-G2). Das hat
    bei BVB-Frankfurt 08.05. dazu gefuehrt dass 0 SAFE-Tipps mehr generiert wurden
    obwohl BVB-Heim @ 1.48 + Lens-Heim @ 1.45 klassische SAFE-Quoten sind.

    Neue Logik: SAFE wird auf VALUE downgegradet NUR WENN aktive Negativ-Signale:
    - Liga in beobachtungs_ligen.json (wirklicher Bluter, schon dort gefiltert)
      ODER
    - Markt-Typ in markt_bluter.json (wirklicher Bluter-Markt)
      ODER
    - SAFE-Quote zu hoch (>1.65 = unsichere SAFE-Range, normaler SAFE liegt 1.30-1.60)
      UND
      keine kompensierenden Goldgrube-Signale (Markt ODER Liga in Goldgrube-Liste)
    Sonst: SAFE bleibt SAFE.

    Effekt: Heim-Sieg-Tipps in BL/Ligue1/Serie A bei klarer Quote bleiben SAFE.
    Fragwuerdige SAFEs (z.B. SAFE auf 2.0-Quote in Beobachtungs-Liga) werden weiter
    ausgefiltert.
    """
    beob_ligen = set(lade_beobachtungs_ligen())
    markt_bluter = set(lade_markt_bluter())
    markt_gold = set(lade_markt_goldgruben())
    liga_gold = set(lade_liga_goldgruben().keys())
    SAFE_QUOTEN_FLOOR = 1.65  # SAFE ist normalerweise 1.30-1.60, ueber 1.65 wird's wackelig

    downgrades = 0
    for spiel in d.get('spiele', []):
        liga = spiel.get('liga') or ''
        sid = spiel.get('id')
        liga_in_beob = liga in beob_ligen or NBA_DECIDER_PATTERN.search(liga)
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat != 'safe':
                continue
            mtyp = markt_typ_pattern(tipp.get('markt') or '')
            try:
                quote = float(tipp.get('quote') or 0)
            except (TypeError, ValueError):
                quote = 0
            grund = None
            if liga_in_beob:
                grund = f"Liga '{liga}' in beobachtungs_ligen"
            elif mtyp in markt_bluter:
                grund = f"Markt-Typ '{mtyp}' in markt_bluter"
            elif quote > SAFE_QUOTEN_FLOOR:
                # Hohe Quote = SAFE darf nur bestehen wenn kompensierende Goldgrube-Signale
                hat_goldgrube = (mtyp in markt_gold) or (liga in liga_gold)
                if not hat_goldgrube:
                    grund = f"Quote {quote} > {SAFE_QUOTEN_FLOOR} ohne Goldgrube-Kompensation"
            if not grund:
                continue
            tipp['kategorie'] = 'value'
            tipp['_safe_confirm_downgrade'] = True
            begr = tipp.get('begruendung') or ''
            tipp['begruendung'] = (begr + f' [Auto: SAFE-Confirm fehlt - {grund}]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), 'value')
            downgrades += 1
    if downgrades:
        print(f"  SAFE-Confirm Filter: {downgrades} SAFE-Tipps auf VALUE downgegradet "
              f"(aktive Negativ-Signale: Beobachtungs-Liga / Markt-Bluter / Quote-Floor)")


# =============================================================================
# Layer-3-Diversifikation + Torschuetzen-Quelle-Validator (08.05.2026)
# =============================================================================

# HR23 (08.05.): max 1 Bein pro Spiel ueber alle Kombis hinweg.
# Layer-1 ist innerhalb 1 Kombi, Layer-2 fuer Sieg-Outcomes, Layer-3 ist die strikteste
# Stufe. Bei Sieg-Outcomes wird hart gedroppt; bei Markt-entkoppelten Doppelungen
# (Tor + Total + BTTS im selben Spiel ueber verschiedene Kombis) nur WARN, weil
# bei wenigen Spielen 4 Kombis sonst nicht baubar sind.

SIEG_MARKT_TOKENS = ('sieg', 'moneyline', '(ml)', '1x2',
                     'doppelte chance', '(1x)', '(x2)', '(12)',
                     ' 1x', ' x2', ' 12', 'oder unentschieden',
                     'spread', 'handicap', '1.hz sieger', 'halbzeit-sieger')


def _markt_ist_sieg_typ(markt):
    if not markt:
        return False
    m = markt.lower()
    return any(t in m for t in SIEG_MARKT_TOKENS)


def validate_layer3(d):
    """HR23 Layer-3 hart erzwingen fuer Sieg-Outcomes.

    Bilanz Stand 08.05.: HR23 wurde heute morgen vom Pattern-Hunter generiert,
    aber das 13:33-Tipps-Routine-Output hatte BVB-Frankfurt-Spiel mit 4 Beinen
    in 4 Kombis. Routine-Prompt ignoriert die Lesson - Mapper muss zwingen.

    Hart-Mode: Sieg-Outcome (Sieg/DC/Spread/Handicap) eines Spiels darf nur in
    1 einziger Kombi sein. Doppelte Sieg-Outcomes droppen wir aus der niedriger
    priorisierten Kombi.

    Soft-Mode: Markt-entkoppelte Doppelungen (Spielertor + Mannschaftssieg in
    verschiedenen Kombis) bleiben drin, nur WARN. Bei wenigen Spielen ist das
    unausweichlich.
    """
    KAT_PRIO = {'safe': 0, 'balance': 1, 'value': 1, 'wackel': 2, 'risk': 3, 'risiko': 3, 'moonshot': 4}
    # spiel_id -> [(kombi-Index, bein-Index, kategorie-prio)]
    sieg_outcome_map = {}
    kombis = d.get('kombis', [])
    for ki, k in enumerate(kombis):
        kat = (k.get('kategorie') or 'value').lower()
        prio = KAT_PRIO.get(kat, 5)
        for bi, b in enumerate(k.get('beine', [])):
            sid = b.get('spiel_id')
            if not sid:
                continue
            if not _markt_ist_sieg_typ(b.get('markt') or ''):
                continue
            sieg_outcome_map.setdefault(sid, []).append((ki, bi, prio))

    # Hart-Drop: pro Spiel-ID alle Sieg-Outcomes ausser dem mit hoechster Prio droppen
    drops = 0
    for sid, eintraege in sieg_outcome_map.items():
        if len(eintraege) <= 1:
            continue
        # Sortiere nach Kategorie-Prio aufsteigend (safe < value < wackel ...)
        eintraege_sorted = sorted(eintraege, key=lambda x: x[2])
        keep_ki = eintraege_sorted[0][0]
        for ki, bi, _ in eintraege_sorted[1:]:
            kombi = kombis[ki]
            beine = kombi.get('beine', [])
            if bi < len(beine):
                bein_str = beine[bi].get('markt', '?')
                kombi_name = kombi.get('name', kombi.get('id', '?'))
                kept_kombi = kombis[keep_ki].get('name', kombis[keep_ki].get('id', '?'))
                print(f"  HR23 Layer-3: Sieg-Outcome '{bein_str}' (Spiel {sid}) aus '{kombi_name}' "
                      f"gedroppt - bleibt nur in '{kept_kombi}' (hoehere Kategorie-Prio)")
                kombi['beine'] = [b for j, b in enumerate(beine) if j != bi]
                # Indizes der nachfolgenden Eintraege im selben Kombi anpassen
                for j, (kj, bj, pj) in enumerate(eintraege_sorted):
                    if kj == ki and bj > bi:
                        eintraege_sorted[j] = (kj, bj - 1, pj)
                drops += 1
    if drops:
        print(f"  HR23 Layer-3: {drops} Sieg-Outcome-Doppelungen ueber Kombis hart gedroppt")
        # Gesamtquote nachziehen passiert in finalize_kombi_quoten() spaeter

    # Soft-WARN: alle Spiele die in mehr als 1 Kombi vorkommen (auch nicht-Sieg)
    spiel_in_kombis = {}
    for ki, k in enumerate(kombis):
        seen = set()
        for b in k.get('beine', []):
            sid = b.get('spiel_id')
            if sid and sid not in seen:
                spiel_in_kombis.setdefault(sid, 0)
                spiel_in_kombis[sid] += 1
                seen.add(sid)
    for sid, n in spiel_in_kombis.items():
        if n > 1:
            print(f"  HR23 Layer-3 WARN: Spiel '{sid}' in {n} Kombis (Markt-entkoppelt - "
                  f"OK bei wenig Spielen, Routine soll bei groesserem Spieltag strikter sein)")


def validate_torschuetze_quelle(d):
    """Halluzinations-Schutz fuer Spielertor-Tipps (08.05.2026 nach Hojlund-Bug).

    Bilanz Stand 08.05.: Routine erfindet Spieler die NICHT zum Verein gehoeren -
    klassisch 'Hojlund' im Frankfurt-Sturm (er spielt fuer ManUtd). Mapper kann
    den Verein nicht selbst pruefen, aber er kann pruefen ob in quellen[] eine
    Verein-Verifikations-URL steht (transfermarkt, kicker, espn-soccer-team,
    bundesliga.com player-Seite). Wenn nicht: WARN-Flag setzen + Tipp auf
    wackel droppen damit er nicht in einzeltipps[] / Hauptkombis steht.

    Quelle-Hosts die als Verein-Verifikation gelten:
    - transfermarkt.com / .de / .us / .co.uk
    - kicker.de
    - espn.com/soccer/team/squad
    - bundesliga.com/.../player/
    - en.eintracht.de/squad oder analog
    - tribuna.com/clubs/.../squad
    - aiscore.com/team-...

    Hartmode: kein Hard-Drop weil False-Positives moeglich (Quellen koennten
    indirekt Spieler bestaetigen). Soft: Tipp auf wackel + Flag.
    """
    QUELLEN_VEREIN = (
        'transfermarkt.com', 'transfermarkt.de', 'transfermarkt.us', 'transfermarkt.co.uk',
        'kicker.de', 'kicker.com',
        'espn.com/soccer/team', 'espn.co.uk/football/team',
        'bundesliga.com', 'premierleague.com', 'laliga.com',
        'eintracht.de/squad', 'fcbayern.com', 'bvb.de', 'cpfc.co.uk', 'manutd.com',
        'tribuna.com/en/clubs', 'aiscore.com/team', 'goal.com/en/team',
        'fotmob.com/teams', 'besoccer.com/team',
    )
    TORSCHUETZE_TOKENS = ('trifft', 'torschuetz', 'jederzeit tor', 'tor (jederzeit)',
                          'doppelpack', 'hattrick')
    downgrades = 0
    for spiel in d.get('spiele', []):
        sk = spiel.get('saison_kontext') or {}
        quellen = sk.get('quellen') or []
        if not isinstance(quellen, list):
            quellen = []
        quellen_str = ' '.join(str(q).lower() for q in quellen)
        hat_verein_quelle = any(h in quellen_str for h in QUELLEN_VEREIN)
        if hat_verein_quelle:
            continue
        # Keine Verein-Verifikations-Quelle vorhanden - alle Torschuetzen-Tipps in
        # diesem Spiel werden wackel (kein Halluzinations-Schutz moeglich)
        sid = spiel.get('id')
        for tipp in spiel.get('tipps', []):
            markt = (tipp.get('markt') or '').lower()
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            if 'punkte' in markt:  # NBA-Player-Punkte ausnehmen
                continue
            if not any(t in markt for t in TORSCHUETZE_TOKENS):
                continue
            tipp['kategorie'] = 'wackel'
            tipp['_torschuetze_quelle_warn'] = True
            begr = tipp.get('begruendung') or ''
            tipp['begruendung'] = (begr + ' [Auto: Torschuetze-Vereins-Quelle (transfermarkt/kicker/'
                                   'espn/bundesliga player-Seite) fehlt in quellen[] - max wackel]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), 'wackel')
            downgrades += 1
    if downgrades:
        print(f"  Torschuetze-Quelle-Filter: {downgrades} Torschuetzen-Tipps auf wackel "
              f"(keine Verein-Verifikations-URL in quellen[] - Halluzinations-Schutz)")


def lade_recherche(datum):
    """Lese data/recherche/<datum>.json wenn existiert.
    Returns: dict mit spielen oder None wenn File fehlt.
    """
    pfad = os.path.join('data', 'recherche', f'{datum}.json')
    if not os.path.exists(pfad):
        # Fallback fuer Vorschau-Files
        for sub in ('recherche_wochenende', 'recherche_woche'):
            alt = os.path.join('data', sub, f'{datum}.json')
            if os.path.exists(alt):
                pfad = alt
                break
        else:
            return None
    try:
        with open(pfad, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _normalize_spielername(name):
    """Normalisiert Spielernamen fuer Squad-Match. Entfernt Sonderzeichen + lowercase.
    'Jonathan Burkardt' -> 'jonathan burkardt'. 'Højlund' -> 'hojlund' (oe-Variante).
    """
    if not name:
        return ''
    # Diakritika-Behandlung simpel: Hoejlund/Højlund/Hojlund -> hojlund
    s = name.lower().strip()
    repl = {'ø': 'o', 'ö': 'o', 'ü': 'u', 'ä': 'a', 'ß': 'ss',
            'é': 'e', 'è': 'e', 'á': 'a', 'à': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ç': 'c'}
    for old, new in repl.items():
        s = s.replace(old, new)
    # Punkte und Bindestriche entfernen
    s = s.replace('.', '').replace('-', ' ')
    return ' '.join(s.split())


def validate_recherche_completeness(d):
    """Prueft ob fuer das Tipps-File ein passendes data/recherche/<datum>.json existiert.
    Wenn ja: pro Spiel im Tipps-File pruefen ob es im Recherche-File ist.
    Spiele OHNE Recherche bekommen ihre Tipps gedroppt (kein Datenfundament).

    Wenn das Recherche-File komplett fehlt: nur WARN, kein Drop (Bootstrap-Phase).
    Spaeter (nach 7 Tagen Live-Betrieb) sollte das Verhalten verschaerft werden.
    """
    datum = d.get('datum')
    if not datum:
        return
    recherche = lade_recherche(datum)
    if not recherche:
        print(f"  Recherche-Completeness: data/recherche/{datum}.json fehlt - Skip "
              f"(Bootstrap-Phase, spaeter verschaerfen)")
        return
    recherche_spiele = {s.get('id'): s for s in recherche.get('spiele', []) if s.get('id')}
    drops = 0
    for spiel in d.get('spiele', []):
        sid = spiel.get('id')
        if sid in recherche_spiele:
            continue
        # Spiel im Tipps aber nicht in Recherche - Tipps droppen
        n_tipps = len(spiel.get('tipps', []))
        if n_tipps:
            spiel['tipps'] = []
            spiel['_recherche_fehlt'] = True
            print(f"  Recherche-Completeness: Spiel '{sid}' nicht in recherche/{datum}.json "
                  f"-> {n_tipps} Tipps gedroppt")
            drops += n_tipps
    if drops:
        print(f"  Recherche-Completeness: {drops} Tipps insgesamt gedroppt (ohne Datenbasis)")


def validate_spieler_squad_match(d):
    """Halluzinations-Schutz Stufe 2 (Recherche-File-basiert):
    Pro Spielertor-Tipp pruefen ob Spielername in squad_heim ODER squad_gast des
    entsprechenden Spiels im Recherche-File steht. Bei Mismatch:
    - Tipp gedropped + Lesson-Eintrag generiert
    - Position-Mismatch (z.B. Spieler in squad mit Position DM/IV/AV/TW als Stuermer-Tipp):
      Tipp downgegraded auf wackel

    Stuermer-Positionen (akzeptabel fuer Torschuetzen-Tipp): ST, MS, LF, RF, ZS, OM,
    LS, RS, RW, LW, LM (Fluegel), CF.
    Defensiv-Positionen (Mismatch fuer Torschuetzen-Tipp): TW, IV, LV, RV, AV, DM, DMF.

    Bootstrap: wenn Recherche-File fehlt, kein Drop - validate_torschuetze_quelle()
    ist die Fallback-Schutz-Stufe.
    """
    datum = d.get('datum')
    if not datum:
        return
    recherche = lade_recherche(datum)
    if not recherche:
        return  # Fallback auf validate_torschuetze_quelle (URL-basiert)
    recherche_spiele = {s.get('id'): s for s in recherche.get('spiele', []) if s.get('id')}
    if not recherche_spiele:
        return

    OFFENSIV_POS = {'st', 'ms', 'lf', 'rf', 'zs', 'om', 'ls', 'rs', 'rw', 'lw',
                    'cf', 'fw', 'attacker', 'striker', 'forward', 'second striker',
                    'centre-forward', 'center-forward', 'wing', 'left wing', 'right wing'}
    # Mittelfeld-Spieler koennen treffen, aber sind Wackel-Material fuer Tor-Tipps
    MITTELFELD_OFFENSIV = {'om', 'zom', 'aom', 'attacking midfielder', 'no.10', '10er',
                           'amf', 'cam', 'lm', 'rm'}
    DEFENSIV_POS = {'tw', 'gk', 'iv', 'cb', 'lv', 'lb', 'rv', 'rb', 'av',
                    'dm', 'dmf', 'cdm', '6er', 'sechser', 'defensive midfielder',
                    'goalkeeper', 'centre-back', 'center-back', 'left-back', 'right-back'}

    TORSCHUETZE_TOKENS = ('trifft', 'torschuetz', 'jederzeit tor', 'tor (jederzeit)',
                          'doppelpack', 'hattrick')
    drops = 0
    downgrades = 0
    for spiel in d.get('spiele', []):
        sid = spiel.get('id')
        recherche_spiel = recherche_spiele.get(sid)
        if not recherche_spiel:
            continue
        squad = (recherche_spiel.get('squad_heim') or []) + (recherche_spiel.get('squad_gast') or [])
        squad_index = {}
        for sp in squad:
            n = _normalize_spielername(sp.get('name', ''))
            if n:
                squad_index[n] = sp

        for tipp in list(spiel.get('tipps', [])):
            markt = (tipp.get('markt') or '').lower()
            if 'punkte' in markt:  # NBA-Player-Punkte, andere Logik
                continue
            if not any(t in markt for t in TORSCHUETZE_TOKENS):
                continue
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value', 'wackel'):
                continue

            # Spieler-Name aus markt extrahieren — heuristisch: erstes/zweites Eigennamen-Token
            # vor "trifft"/"Tor"/"Doppelpack". Wir versuchen: alle Wort-Tokens vor diesen Keywords.
            import re as _re
            name_part = _re.split(r'\b(trifft|torschuetz|jederzeit|tor|doppelpack|hattrick|2\+)\b',
                                  tipp.get('markt', ''), flags=_re.IGNORECASE)[0]
            # Markt kann mit "Spielname: Spielername " starten - Doppelpunkt-Split
            if ':' in name_part:
                name_part = name_part.rsplit(':', 1)[-1]
            spielername = _normalize_spielername(name_part)
            if not spielername or len(spielername) < 3:
                continue  # Konnte Namen nicht parsen, kein Drop

            # Squad-Match (toleriert Teilnamen-Match: 'jonathan burkardt' -> 'burkardt' in squad)
            squad_match = None
            for sname, sdata in squad_index.items():
                if spielername == sname:
                    squad_match = sdata
                    break
                # Teilnamen: letztes Wort des Tipps in squad-Name oder umgekehrt
                tipp_tokens = spielername.split()
                squad_tokens = sname.split()
                if tipp_tokens and squad_tokens:
                    if tipp_tokens[-1] == squad_tokens[-1] and len(tipp_tokens[-1]) >= 4:
                        squad_match = sdata
                        break

            if not squad_match:
                # Halluzination - Spieler nicht im Squad
                spiel['tipps'].remove(tipp)
                tid = tipp.get('id')
                if tid:
                    d['einzeltipps'] = [e for e in d.get('einzeltipps', [])
                                       if not (e.get('spiel_id') == sid and e.get('tipp_id') == tid)]
                print(f"  Spieler-Squad-Match: Tipp '{tipp.get('markt')}' gedroppt - "
                      f"Spieler '{spielername}' nicht in squad_heim/gast von {sid}")
                drops += 1
                continue

            # Position-Check
            pos = (squad_match.get('position') or '').lower().strip()
            if pos in DEFENSIV_POS and kat in ('safe', 'value'):
                tipp['kategorie'] = 'wackel'
                tipp['_squad_position_downgrade'] = True
                begr = tipp.get('begruendung') or ''
                tipp['begruendung'] = (begr + f" [Auto: Squad-Pos '{pos}' (defensiv) - "
                                       f"Torschuetzen-Tipp max wackel]").strip()
                _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), 'wackel')
                downgrades += 1
    if drops:
        print(f"  Spieler-Squad-Match: {drops} Halluzinations-Tipps gedroppt")
    if downgrades:
        print(f"  Spieler-Squad-Match: {downgrades} Tipps wegen Defensiv-Position auf wackel")


def finalize_kombi_quoten(d):
    """Berechne gesamtquote + rechnung fuer alle Kombis neu falls leer/inkonsistent.
    Droppe Kombis ohne Beine (z.B. wenn Layer-3 alle Beine entfernt hat).

    Routine schreibt das Feld manchmal als 'gesamt_quote' (Underscore - jetzt via
    KOMBI_RENAMES gemappt) oder gar nicht. Dieser Validator stellt sicher dass nach
    allen Validators (die Beine droppen koennen) die finale Quote stimmt UND
    leere Kombi-Eintraege nicht im UI als Geister-Zeile auftauchen.
    """
    fixed = 0
    kept = []
    dropped_empty = 0
    for k in d.get('kombis', []):
        beine = k.get('beine', [])
        if not beine:
            dropped_empty += 1
            print(f"  Kombi '{k.get('name', k.get('id', '?'))}' gedroppt: keine Beine mehr "
                  f"(z.B. nach Layer-3-Filter)")
            continue
        try:
            quoten = [float(b.get('quote') or 0) for b in beine]
            if any(q <= 0 for q in quoten):
                kept.append(k)  # Quote-Bug - nicht recalculiert aber Kombi bleibt
                continue
            neu = 1.0
            for q in quoten:
                neu *= q
            neu = round(neu, 2)
        except (ValueError, TypeError):
            kept.append(k)
            continue
        alt = k.get('gesamtquote')
        try:
            alt_float = float(alt) if alt is not None else None
        except (ValueError, TypeError):
            alt_float = None
        if alt_float is None or abs(alt_float - neu) > 0.05:
            k['gesamtquote'] = neu
            quoten_str = ' x '.join(f"{q:.2f}" for q in quoten)
            k['rechnung'] = f"{quoten_str} = {neu}"
            fixed += 1
        # Kombi-Name an finale Quote anpassen falls Name "(~Xx)"-Suffix hat aber Quote anders
        # Beispiel: 'Risiko-Kombi (~15.30x)' bei gesamtquote=22.63 -> 'Risiko-Kombi (~22.63x)'
        import re as _re_kn
        name = k.get('name', '')
        name_match = _re_kn.match(r'^(.+?)\s*\(~([\d.]+)x\)\s*$', name)
        if name_match:
            base_name = name_match.group(1)
            try:
                name_quote = float(name_match.group(2))
                if abs(name_quote - neu) > 0.5:
                    k['name'] = f"{base_name} (~{neu:.2f}x)"
            except (ValueError, TypeError):
                pass
        kept.append(k)
    d['kombis'] = kept
    if fixed:
        print(f"  Gesamtquote-Auto-Compute: {fixed} Kombis neu berechnet")
    if dropped_empty:
        print(f"  Leere Kombis gedroppt: {dropped_empty}")


# =============================================================================
# Hartregeln aus User-Review v23 (04.05.2026): Chelsea-Forest 1:3-Lehre
# =============================================================================

def _team_kern(team_name):
    """Extrahiert das Kern-Wort aus einem Team-Namen fuer Pattern-Match.
    'Chelsea FC' -> 'chelsea'. 'Borussia Moenchengladbach' -> 'moenchengladbach' (laengstes Wort).
    'AS Roma' -> 'roma'. 'AC Milan' -> 'milan'. 'New York Knicks' -> 'knicks'.
    Generic-Suffixe FC/AC/AS/SC/SV/CF werden ignoriert."""
    if not team_name:
        return ''
    GENERIC = {'fc', 'ac', 'as', 'sc', 'sv', 'cf', 'fk', 'kk', 'rcd', 'us', 'fce', 'ssc', 'ssv',
               'tsg', 'vfb', 'vfl', '1.', '04', '05', '07', '09', '96', '98',
               'borussia', 'real', 'inter', 'athletic', 'atletico', 'olympic', 'olympique',
               'new', 'old', 'royal', 'rcd', 'real'}
    woerter = [w.lower().strip('.()') for w in team_name.split() if len(w) >= 3]
    # Filter generic
    kandidaten = [w for w in woerter if w not in GENERIC]
    if not kandidaten:
        kandidaten = woerter or [team_name.lower()]
    # Laengstes uebrig
    return max(kandidaten, key=len) if kandidaten else team_name.lower()


# HR2 (Anti-Heim-Bias): Pattern fuer Heim-Form-Krise im saison_kontext.
HEIM_KRISE_PATTERNS = (
    'heim-pleite', 'heim pleite', 'heimpleite', 'heim-niederlage',
    'pleiten serie', 'pleiten-serie', 'niederlagen-serie', 'niederlagen serie',
    'heim-krise', 'heim krise', 'heimkrise',
    'spielen ohne sieg', 'spiele ohne sieg',
    'spielen ohne tor', 'spiele ohne tor',
    'sturm-krise', 'sturm krise', 'tor-flaute', 'torflaute',
    '5 heim', '6 heim', '4 heim',  # "5 Heimpleiten in Folge" etc.
)

# HR3 (Joker-Stuermer): Pattern fuer Doppelbelastungs-Rotation.
ROTATION_PATTERNS = (
    'rotier', 'rotation wahrscheinlich', 'rotation moeglich',
    'b-elf', 'reservisten', 'stamm-elf koennte ruhen',
    'auswechslungs-wahrscheinlichkeit', 'koennte rotiert', 'koennte ausgewechselt',
)

# HR4 (Story-Konflikt v2) - Konflikt-Tokens pro Markt-Familie.
KONFLIKT_HEIM_TIPPEN = HEIM_KRISE_PATTERNS  # Heim-Tipps blockieren wenn Heim-Krise erwaehnt
KONFLIKT_TOPSTUERMER_TIPPEN = ROTATION_PATTERNS  # Top-Stuermer-Tipps blockieren bei Rotation
KONFLIKT_SAFE_KOMFORT_PATTERNS = (
    'saisonziel erreicht', 'saisonziel durch', 'gerettet', 'uneinholbar',
    'kein druck mehr', 'nichts mehr zu spielen', 'klassenerhalt durch',
    'mid-table-auslauf', 'spielbetrieb ohne ziel',
)

# HR6 (Auswaerts-Auto-VALUE): Schwellen.
AUSWAERTS_AUTOSAFE_MIN_UNBESIEGT = 6
AUSWAERTS_AUTOSAFE_MIN_TORSERIE = 6


def validate_heim_form(d):
    """HR2: Anti-Heim-Bias bei Form-Realitaet (User-Review v23 04.05.2026).

    EMPIRIE Chelsea-Forest 1:3: Chelsea Heim-Favorit @ 1.73 mit 5 Heim-Pleiten Serie
    + Sturm-Krise. App labelte trotzdem Chelsea-DC + Palmer-Tor als VALUE. Beide tot.
    Forest auswaerts 9 Spiele unbesiegt - Spiegel-Tipp (Forest-Sieg @ 7.00) komplett
    uebersehen.

    Hartregel: Wenn saison_kontext erwaehnt 'Heim-Krise'/'Pleiten-Serie'/'Sturm-Krise'
    -> Heim-Sieg/-DC/-Top-Stuermer-Tipps werden auf wackel gedroppt (nicht VALUE/SAFE).
    Tor-Aggregat-Tipps (BTTS, Ueber/Unter Tore-Total) bleiben unberuehrt.
    """
    sieg_dc_marker = ('sieg', '(ml)', 'moneyline', '1x2',
                      'doppelte chance', '(1x)', '(x2)', '(12)',
                      ' 1x', ' x2', ' 12', 'oder unentschieden',
                      'spread', 'handicap')
    torschuetze_marker = ('trifft', 'torschuetz', 'jederzeit tor',
                          'doppelpack', 'hattrick', 'tor (jederzeit)')
    downgrades = 0
    for spiel in d.get('spiele', []):
        sk = spiel.get('saison_kontext') or {}
        # Suche Heim-Krise in allen relevanten Text-Feldern
        scan_text = ' '.join([
            (sk.get('saisonziel_heim') or ''),
            (sk.get('motivations_asymmetrie') or ''),
            (sk.get('heim_form_letzte_5') or ''),
            (sk.get('heim_serie') or ''),
        ]).lower()
        if not any(p in scan_text for p in HEIM_KRISE_PATTERNS):
            continue
        heim_kern = _team_kern(spiel.get('heim') or '')
        sid = spiel.get('id')
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            markt = (tipp.get('markt') or '').lower()
            # Heim-Sieg/-DC-Tipp = enthaelt Heim-Kern-Wort + Sieg-Marker
            ist_heim_sieg_dc = heim_kern and heim_kern in markt and any(s in markt for s in sieg_dc_marker)
            # Heim-Torschuetze = Torschuetzen-Markt mit Heim-Bezug (heuristisch)
            # Wir nehmen an: jeder Torschuetzen-Tipp ohne Gast-Erwaehnung ist Heim-Spieler.
            # Genauer: spielt das Heim-Team auf den Top-Stuermer? Pruefe ob markt-Spieler
            # im saison_kontext heim-bezogen.
            ist_torschuetze = any(t in markt for t in torschuetze_marker)
            # Konservativ: Torschuetzen-Tipps werden nur dann gedroppt wenn explizit
            # Heim-Sturm-Krise erwaehnt wird (heim_tore_letzte_5<4 oder 'sturm-krise').
            heim_sturm_krise = ('sturm-krise' in scan_text or 'sturm krise' in scan_text
                                or 'tor-flaute' in scan_text or 'torflaute' in scan_text
                                or 'spielen ohne tor' in scan_text or 'spiele ohne tor' in scan_text)
            if not (ist_heim_sieg_dc or (ist_torschuetze and heim_sturm_krise)):
                continue
            tipp['kategorie'] = 'wackel'
            tipp['_heim_form_block'] = True
            begr = tipp.get('begruendung') or ''
            tipp['begruendung'] = (begr + ' [Auto HR2: Heim-Krise/Sturm-Krise erkannt - Heim-Sieg/-DC/-Top-Stuermer max WACKEL]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), 'wackel')
            downgrades += 1
    if downgrades:
        print(f"  HR2 Heim-Form-Block: {downgrades} Heim-Sieg/DC/Torschuetzen-Tipps auf WACKEL "
              f"(Heim-Krise/Pleiten-Serie/Sturm-Krise im saison_kontext erkannt)")


def validate_doppelbelastung_joker(d):
    """HR3: Joker-Stuermer statt Top-Stuermer bei UEFA-Doppelbelastung.

    EMPIRIE Chelsea-Forest 04.05.: App-Begruendung schrieb selbst 'Wood koennte rotiert
    werden wegen EL-Rueckspiel'. Trotzdem Wood @ 3.50 als WACKEL getippt. Awoniyi
    (Backup) traf doppelt @ 4.00.

    Hartregel: Wenn parallel_heim/gast UEFA-Spiel innerhalb 4 Tagen UND
    motivations_asymmetrie 'rotier'-Token enthaelt -> Top-Stuermer-Torschuetzen-Tipp
    auf max WACKEL (kein VALUE/SAFE moeglich, weil Auswechslungs-Risiko nicht ignorierbar).
    """
    torschuetze_marker = ('trifft', 'torschuetz', 'jederzeit tor',
                          'doppelpack', 'hattrick', 'tor (jederzeit)')
    uefa_marker = ('cl-', 'cl ', 'champions league', 'el-', 'el ', 'europa league',
                   'conference', 'uefa')
    downgrades = 0
    for spiel in d.get('spiele', []):
        sk = spiel.get('saison_kontext') or {}
        parallel_heim = (sk.get('parallel_heim') or '').lower()
        parallel_gast = (sk.get('parallel_gast') or '').lower()
        asym = (sk.get('motivations_asymmetrie') or '').lower()
        recov_text = ((sk.get('recovery_heim') or '') + ' ' + (sk.get('recovery_gast') or '')).lower()
        # Doppelbelastung erkannt?
        hat_uefa_parallel = any(u in parallel_heim for u in uefa_marker) \
                         or any(u in parallel_gast for u in uefa_marker)
        # Tage-Schwelle: '4 tage', '3 tage', '2 tage' bei recovery oder parallel
        eng_takt = any(t in recov_text or t in parallel_heim or t in parallel_gast
                       for t in ('2 tage', '3 tage', '4 tage'))
        rotation_erwartet = any(p in asym for p in ROTATION_PATTERNS) \
                         or any(p in recov_text for p in ROTATION_PATTERNS)
        if not (hat_uefa_parallel and eng_takt and rotation_erwartet):
            continue
        sid = spiel.get('id')
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            markt = (tipp.get('markt') or '').lower()
            if not any(t in markt for t in torschuetze_marker):
                continue
            # Top-Stuermer (heuristisch: niedrige Quote = wahrscheinlich Top-Stuermer)
            try:
                quote = float(tipp.get('quote') or 99)
            except (TypeError, ValueError):
                quote = 99
            if quote >= 3.5:
                # Backup-Stuermer-Quote-Range - nicht runter, evtl. sogar VALUE-faehig
                continue
            tipp['kategorie'] = 'wackel'
            tipp['_joker_top_stuermer_block'] = True
            begr = tipp.get('begruendung') or ''
            tipp['begruendung'] = (begr + ' [Auto HR3: UEFA-Doppelbelastung + Rotation - Top-Stuermer max WACKEL, Joker-Tipp suchen]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), 'wackel')
            downgrades += 1
    if downgrades:
        print(f"  HR3 Joker-Trigger: {downgrades} Top-Stuermer-Torschuetzen-Tipps auf WACKEL "
              f"(UEFA-Doppelbelastung + Rotation erkannt)")


def validate_story_konflikt_v2(d):
    """HR4: Story-Konflikt-Check v2 (Erweiterung Hebel S aus User-Review v23).

    Bestehender Hebel S faengt nur 'edge kleiner als'/'eher 50/50' ab. v2 scannt
    konkrete Pattern in begruendung[] selbst:
    - Tipp Heim-Sieg/-DC + Begruendung 'Pleiten-Serie'/'Heim-Krise' -> max WACKEL
    - Tipp Top-Stuermer-Tor + Begruendung 'rotier'/'ausgewechselt' -> max WACKEL
    - SAFE + Begruendung 'Saisonziel erreicht'/'gerettet'/'uneinholbar' -> max VALUE
    """
    sieg_dc_marker = ('sieg', '(ml)', 'moneyline', '1x2',
                      'doppelte chance', '(1x)', '(x2)', '(12)',
                      ' 1x', ' x2', 'oder unentschieden')
    torschuetze_marker = ('trifft', 'torschuetz', 'jederzeit tor',
                          'doppelpack', 'hattrick')
    downgrades = 0
    for spiel in d.get('spiele', []):
        sid = spiel.get('id')
        heim_kern = _team_kern(spiel.get('heim') or '')
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            markt = (tipp.get('markt') or '').lower()
            begr = (tipp.get('begruendung') or '').lower()
            if not begr:
                continue
            ist_heim_sieg_dc = heim_kern and heim_kern in markt and any(s in markt for s in sieg_dc_marker)
            ist_torschuetze = any(t in markt for t in torschuetze_marker)
            try:
                quote = float(tipp.get('quote') or 99)
            except (TypeError, ValueError):
                quote = 99
            ist_top_stuermer = ist_torschuetze and quote < 3.5
            grund = None
            if ist_heim_sieg_dc and any(p in begr for p in KONFLIKT_HEIM_TIPPEN):
                grund = 'Heim-Krise-Token in eigener Begruendung'
            elif ist_top_stuermer and any(p in begr for p in KONFLIKT_TOPSTUERMER_TIPPEN):
                grund = 'Rotations-Token bei Top-Stuermer-Tipp'
            elif kat == 'safe' and any(p in begr for p in KONFLIKT_SAFE_KOMFORT_PATTERNS):
                grund = 'Komfort-Pattern bei SAFE'
            if not grund:
                continue
            neue_kat = 'wackel' if kat in ('safe', 'value') and grund.startswith(('Heim-Krise', 'Rotations')) else 'value'
            tipp['kategorie'] = neue_kat
            tipp['_story_konflikt_v2'] = True
            tipp['begruendung'] = (tipp.get('begruendung','') + f' [Auto HR4: Story-Konflikt v2 ({grund}) -> {kat}->{neue_kat}]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), neue_kat)
            downgrades += 1
    if downgrades:
        print(f"  HR4 Story-Konflikt v2: {downgrades} Tipps eine Stufe runter "
              f"(eigene Begruendung widerspricht der Kategorie)")


def validate_auswaerts_auto_value(d):
    """HR6: Auswaerts-Form-Auto-VALUE-Detektor (User-Review v23 04.05.).

    EMPIRIE Forest 04.05.: 9 Spiele unbesiegt + 8/8 Auswaerts-Tor-Serie + EL-Druck.
    App hat KEINEN Forest-Sieg-Tipp gesetzt. Forest-Sieg @ 7.00 traf.

    Hartregel: Wenn gast_form-Pflichtfelder anzeigen >=6 Unbesiegt UND >=6 Auswaerts-
    Tor-Serie UND saisonziel_gast Druck-Token enthaelt -> warnung-Log dass Auswaerts-
    VALUE-Tipp fehlen koennte. Mapper kann nichts hinzufuegen aber warnt.
    """
    druck_tokens = ('cl-quali', 'champions-league-quali', 'el-quali', 'europa-league-quali',
                    'klassenerhalt', 'abstiegskampf', 'pflichtsieg', 'must-win',
                    'titel-rennen', 'meister', 'aufstieg')
    fehlende_auto_value = []
    for spiel in d.get('spiele', []):
        sk = spiel.get('saison_kontext') or {}
        # Pflichtfelder-Heuristik: aus Strings parsen
        unbesiegt_serie = (sk.get('gast_serie') or '').lower()
        tor_serie = (sk.get('gast_auswaerts_tor_serie') or '').lower() if isinstance(sk.get('gast_auswaerts_tor_serie'), str) else ''
        ziel = (sk.get('saisonziel_gast') or '').lower()
        # int-Felder (neuere Routinen)
        try:
            unbesiegt_int = int(sk.get('gast_unbesiegt_serie') or 0)
        except (TypeError, ValueError):
            unbesiegt_int = 0
        try:
            tor_int = int(sk.get('gast_auswaerts_tor_serie_int') or 0)
        except (TypeError, ValueError):
            tor_int = 0
        # String-Heuristik
        unbesiegt_match = any(s in unbesiegt_serie for s in ('6 spiele unbesiegt', '7 spiele unbesiegt',
                                                              '8 spiele unbesiegt', '9 spiele unbesiegt',
                                                              '10 spiele unbesiegt'))
        tor_match = any(s in tor_serie for s in ('6/', '7/', '8/', '9/', '10/'))
        druck_match = any(t in ziel for t in druck_tokens)
        kriterium_erfuellt = (unbesiegt_match or unbesiegt_int >= 6) \
                          and (tor_match or tor_int >= 6) \
                          and druck_match
        if not kriterium_erfuellt:
            continue
        # Pruefe ob ein Auswaerts-Sieg/-DC-Tipp existiert
        gast_kern = _team_kern(spiel.get('gast') or '')
        hat_gast_value = False
        for t in spiel.get('tipps', []):
            kat = (t.get('kategorie') or '').lower()
            markt = (t.get('markt') or '').lower()
            if kat in ('safe', 'value') and gast_kern and gast_kern in markt and ('sieg' in markt or 'oder unentschieden' in markt or 'x2' in markt):
                hat_gast_value = True
                break
        if not hat_gast_value:
            fehlende_auto_value.append(f"{spiel.get('heim')}-{spiel.get('gast')}")
    if fehlende_auto_value:
        print(f"  HR6 Auswaerts-Auto-VALUE WARN: {len(fehlende_auto_value)} Spiele mit "
              f"klarem Gast-Form-Edge OHNE Gast-VALUE-Tipp: {fehlende_auto_value[:3]}"
              f"{'...' if len(fehlende_auto_value)>3 else ''}")


# Pattern fuer Hebel S (validate_saison_kontext_sanity).
# Es werden NUR die Synthese-Felder motivations_asymmetrie + recovery_heim/gast
# gescannt - nicht die saisonziel-Felder. Saisonziel ist Fakt; ob das Edge-Implikation
# hat, schreibt die Routine selbst in motivations_asymmetrie. Damit halluziniert
# der Mapper keine Edge-Reduzierung wo die Routine selbst klare Edge sieht
# (z.B. BOU-CRY 03.05.: Routine sagt 'Bournemouth profitiert von B-Elf-Palace' -
# das ist Edge PRO Bournemouth, nicht gegen).

# Direkte Edge-Reduzierungs-Aussagen in motivations_asymmetrie.
NEGATIVE_EDGE_PATTERNS = (
    'edge kleiner als', 'edge daher kleiner', 'edge geringer als',
    'kleiner als suggeriert', 'kleiner als die heim',
    'eher 50/50', 'eher coinflip', 'eher remis', 'eher 50:50',
    'moeglicherweise nicht', 'edge unklar', 'edge schwer',
    'achtung', 'vorsicht', 'ueberraschungs-risiko',
    'klassen-edge schwankt', 'klassen-edge kleiner',
    'kein klarer favorit', 'unklarer favorit',
)
# Direkte Belastungs-Aussagen in recovery-Feldern (nicht generisch '3 Tage Pause').
RECOVERY_WARNUNG_PATTERNS = (
    'muede', 'mude', 'ermuedet', 'ermuedung', 'belastung hoch', 'belastung sehr hoch',
    'recovery kritisch', 'spielt halbtags',
    'cl-doppelbelastung', 'el-doppelbelastung', 'pokal-doppelbelastung',
    'rotiert vor', 'starke rotation', 'rotation erwartet',
)


def validate_saison_kontext_sanity(d):
    """ROI-SANIERUNG Hebel S 04.05.2026: Saison-Kontext-Sanity-Check.

    Lehre aus 03.05.2026 BMG-BVB + Freiburg-Wolfsburg: Routine recherchiert den
    saison_kontext{}-Block korrekt, ignoriert ihn dann aber bei Kategorie-Vergabe.
    BMG-BVB: Routine schrieb 'Klassenerhalt faktisch durch + Vize hinter
    uneinholbarem Bayern' und labelte SAFE auf BVB-DC -> Endstand 1:0 fuer BMG.
    Freiburg-Wolfsburg: Routine schrieb 'Edge daher kleiner als Heimstaerke
    suggeriert' und labelte trotzdem SAFE auf Freiburg-DC -> 1:1.

    Logik: SAFE/VALUE auf Sieg/DC/Spread werden eine Stufe runter wenn die
    Routine in motivations_asymmetrie SELBST Edge-Reduzierung formuliert
    ('edge kleiner als suggeriert', 'eher 50/50', 'achtung', 'vorsicht') ODER
    in recovery_heim/gast explizite Belastungs-Pattern stehen
    ('mude', 'ermuedet', 'CL-doppelbelastung', 'rotiert vor').

    Pattern wurden bewusst eng gehalten - nur direkte Edge-Reduzierungs-Aussagen,
    keine breiten Komfort-Wortfelder. Saisonziel-Felder werden gar nicht gescannt
    (Routine kann Komfort-Status auf der Underdog-Seite haben und das ist Edge
    PRO Tipp-Team, nicht gegen). Tor-Maerkte (BTTS, Ueber/Unter, Torschuetzen)
    sind ausgenommen - das sind keine Sieg-Tipps.
    """
    sieg_marker_lower = ('sieg', 'moneyline', '(ml)', '(1x2)', '1x2',
                         'doppelte chance', '(1x)', '(x2)', '(12)',
                         ' 1x', ' x2', ' 12', 'spread', 'handicap')
    downgrades = 0
    for spiel in d.get('spiele', []):
        sk = spiel.get('saison_kontext') or {}
        asym   = (sk.get('motivations_asymmetrie') or '').lower()
        recov_h = (sk.get('recovery_heim') or '').lower()
        recov_g = (sk.get('recovery_gast') or '').lower()

        asym_match      = any(p in asym for p in NEGATIVE_EDGE_PATTERNS)
        belastung_match = any(p in recov_h for p in RECOVERY_WARNUNG_PATTERNS) \
                       or any(p in recov_g for p in RECOVERY_WARNUNG_PATTERNS)

        if not (asym_match or belastung_match):
            continue

        # Trigger-Grund fuers Logging
        gruende = []
        if asym_match:       gruende.append('Asymmetrie-Warnung (Routine sagt selbst Edge kleiner)')
        if belastung_match:  gruende.append('Belastungs-Warnung (Recovery)')
        grund_str = ' / '.join(gruende)

        sid = spiel.get('id')
        for tipp in spiel.get('tipps', []):
            kat = (tipp.get('kategorie') or '').lower()
            if kat not in ('safe', 'value'):
                continue
            markt_lower = (tipp.get('markt') or '').lower()
            # Nur Sieg/DC/Spread-Tipps degradieren - Tor-Maerkte sind unabhaengig
            ist_sieg_tipp = any(m in markt_lower for m in sieg_marker_lower)
            if not ist_sieg_tipp:
                continue
            neue_kat = 'value' if kat == 'safe' else 'wackel'
            tipp['kategorie'] = neue_kat
            tipp['_saison_kontext_sanity_downgrade'] = True
            begr = tipp.get('begruendung') or ''
            tipp['begruendung'] = (begr + f' [Auto: Saison-Kontext-Sanity - {grund_str} -> {kat}->{neue_kat}]').strip()
            _sync_einzeltipp_kategorie(d, sid, tipp.get('id'), neue_kat)
            downgrades += 1
    if downgrades:
        print(f"  Saison-Kontext-Sanity Filter: {downgrades} Sieg/DC-Tipps eine Stufe runter "
              f"(Komfort-Status/Asymmetrie/Belastungs-Pattern in saison_kontext erkannt)")


# Markt-Klassifikation fuer Hebel M (validate_markt_mix).
def _klass_markt(markt):
    """Returns: 'dc', 'sieg', 'torschuetze', 'tor_total', 'btts', 'spread', 'spieler', 'sonstige'"""
    if not markt:
        return 'sonstige'
    m = markt.lower()
    if 'doppelte chance' in m or '(1x)' in m or '(x2)' in m or '(12)' in m \
       or ' dc ' in f' {m} ' or 'oder unentschieden' in m or 'unentschieden oder' in m:
        return 'dc'
    if ('trifft' in m or 'torschuetz' in m or 'jederzeit tor' in m
            or 'tor (jederzeit)' in m or 'doppelpack' in m or 'hattrick' in m) \
       and 'punkte' not in m:
        return 'torschuetze'
    if ('tore' in m or ' tor ' in f' {m} ') \
       and ('ueber' in m or 'über' in m or 'unter' in m or 'mehr als' in m or 'weniger als' in m):
        return 'tor_total'
    if 'beide teams treffen' in m or 'btts' in m:
        return 'btts'
    if 'spread' in m or 'handicap' in m:
        return 'spread'
    if 'punkte' in m and ('ueber' in m or 'über' in m or 'unter' in m or 'mehr als' in m or 'weniger als' in m):
        return 'spieler'
    if m.endswith(' sieg') or ' sieg ' in f' {m} ' or 'moneyline' in m or '(ml)' in m or '1x2' in m:
        return 'sieg'
    return 'sonstige'


def validate_markt_mix(d):
    """ROI-SANIERUNG Hebel M 04.05.2026: Markt-Mix-Pflicht pro Spiel.

    Lehre aus 03.05.2026 St.Pauli-Mainz: Routine packte 3 defensive Tipps
    (Unter 2.5, Mainz-DC, BTTS-NEIN) auf ein Spiel das Mainz 1:2 auswaerts
    gewann. Mainz-Sieg + BTTS-Ja + Ueber 1.5 + Mainz-Torschuetze waeren alle
    rein - alles ignoriert. Bilanz Spiel: -2 Units.

    Regeln:
    1. Max 1 DC-Tipp pro Spiel. Mehrfach-DC ist Konfidenz-Theater - droppe
       alle bis auf den hoechstpriorisierten (Kategorie + Edge).
    2. Wenn ein Spiel KEINEN Sieg-Tipp UND KEINEN Torschuetzen-Tipp hat
       (also nur DC/Total/BTTS/Spread/Spieler/Sonstige): die Routine hat sich
       auf rein defensive Maerkte beschraenkt -> kein offensives Edge-Signal.
       SAFE-DC-Tipps in solchen Spielen werden auf VALUE downgegradet.
    """
    drops_doppel_dc = 0
    safe_dc_downgrades = 0
    for spiel in d.get('spiele', []):
        tipps = spiel.get('tipps', [])
        if not tipps:
            continue
        # Klassifizierung pro Tipp
        klass = [(t, _klass_markt(t.get('markt') or '')) for t in tipps]

        # Regel 1: max 1 DC-Tipp pro Spiel
        dc_tipps = [(t, k) for t, k in klass if k == 'dc']
        if len(dc_tipps) > 1:
            # Sortiere nach Kategorie-Prio (safe vor value vor wackel) + edge_prozent
            kat_prio = {'safe': 0, 'value': 1, 'wackel': 2, 'risk': 3, 'moonshot': 4}
            def _score(item):
                t, k = item
                kat = (t.get('kategorie') or 'wackel').lower()
                try:
                    e = float(t.get('edge_prozent') or 0)
                except (ValueError, TypeError):
                    e = 0
                return (kat_prio.get(kat, 5), -e)
            dc_sorted = sorted(dc_tipps, key=_score)
            kept_dc = dc_sorted[0][0]
            drop_ids = {id(t) for t, _ in dc_sorted[1:]}
            sid = spiel.get('id')
            new_tipps = []
            for t in tipps:
                if id(t) in drop_ids:
                    drops_doppel_dc += 1
                    print(f"  Markt-Mix: DC-Doppel '{t.get('markt')}' aus Spiel '{sid}' gedroppt "
                          f"(behalte '{kept_dc.get('markt')}')")
                    # Auch aus einzeltipps[] entfernen
                    tid = t.get('id')
                    d['einzeltipps'] = [e for e in d.get('einzeltipps', [])
                                        if not (e.get('spiel_id') == sid and e.get('tipp_id') == tid)]
                else:
                    new_tipps.append(t)
            spiel['tipps'] = new_tipps
            klass = [(t, _klass_markt(t.get('markt') or '')) for t in spiel['tipps']]

        # Regel 2: kein Sieg + kein Torschuetze = defensives Spiel
        # -> SAFE auf DC ist nicht legitim (kein offensives Edge-Signal)
        klassen_set = {k for _, k in klass}
        hat_offensive_signal = ('sieg' in klassen_set) or ('torschuetze' in klassen_set)
        if not hat_offensive_signal:
            sid = spiel.get('id')
            for t, k in klass:
                if k == 'dc' and (t.get('kategorie') or '').lower() == 'safe':
                    t['kategorie'] = 'value'
                    t['_markt_mix_dc_downgrade'] = True
                    begr = t.get('begruendung') or ''
                    t['begruendung'] = (begr + ' [Auto: Markt-Mix - kein Sieg/Torschuetzen-Tipp '
                                        'im Spiel, also kein offensives Edge-Signal -> SAFE-DC nicht legitim]').strip()
                    _sync_einzeltipp_kategorie(d, sid, t.get('id'), 'value')
                    safe_dc_downgrades += 1
    if drops_doppel_dc:
        print(f"  Markt-Mix: {drops_doppel_dc} DC-Doppel-Tipps gedroppt (max 1 DC pro Spiel)")
    if safe_dc_downgrades:
        print(f"  Markt-Mix: {safe_dc_downgrades} SAFE-DC-Tipps auf VALUE downgegradet "
              f"(Spiel ohne Sieg/Torschuetzen-Tipp = rein defensiv)")


def validate_dossier_quality(d):
    """Pre-Push-Quality-Check (Hebel Q 04.05.2026): scannt das gesamte Dossier
    GANZHEITLICH und warnt vor strukturellen Problemen die einzelne Validatoren
    nicht sehen. Loggt Warnungen - Mapper kann nichts anfuegen, nur User soll
    es beim Lesen merken + Routine kann es beim naechsten Lauf vermeiden.

    Quality-Checks:
    1. Markt-Mix in einzeltipps[]: max 40% DC, mindestens 25% Torschuetzen ODER Sieg
    2. Pro Spiel mit Heim-Sieg-Quote < 1.80: warne wenn KEIN Torschuetzen-Tipp dabei
       (Goldgrube +24% ROI ignoriert)
    3. Wenn Dossier nur 0-1 SAFE-Tipps enthaelt: warne wenn auch viele VALUE-Tipps
       (Routine zoegert oder Mapper hat alles gefiltert)
    """
    einzel = d.get('einzeltipps') or []
    if not einzel:
        return
    n_dc = n_torschuetze = n_sieg = n_total_off = 0
    for e in einzel:
        markt = (e.get('markt') or '').lower()
        if 'doppelte chance' in markt or 'oder unentschieden' in markt or '(1x)' in markt or '(x2)' in markt:
            n_dc += 1
        if any(k in markt for k in ('trifft', 'torschuetz', 'jederzeit tor', 'doppelpack', 'hattrick')) and 'punkte' not in markt:
            n_torschuetze += 1
            n_total_off += 1
        if any(k in markt for k in ('sieg', 'moneyline', '(ml)', 'spread', 'handicap')):
            n_sieg += 1
            n_total_off += 1
    n = len(einzel)
    dc_pct = n_dc / n * 100 if n else 0
    off_pct = n_total_off / n * 100 if n else 0

    # 1. DC-Inflations-Check
    if dc_pct > 40:
        print(f"  Pre-Push-Quality WARN: {n_dc}/{n} Einzeltipps sind DC ({dc_pct:.0f}%) - "
              f"zu defensiv. Routine soll mehr Torschuetzen/Sieg-Tipps suchen.")

    # 2. Offensiv-Anteil-Check
    if n >= 5 and off_pct < 25:
        print(f"  Pre-Push-Quality WARN: nur {n_total_off}/{n} offensive Tipps ({off_pct:.0f}%) - "
              f"Goldgrube Torschuetzen Jederzeit (+24% ROI) wird ignoriert.")

    # 3. Pro Heim-Favorit-Spiel: kein Torschuetze = WARN
    fehlende_torschuetzen_spiele = []
    for spiel in d.get('spiele', []):
        spiel_tipps = spiel.get('tipps', [])
        # Heuristik: Heim-Favorit-Spiel = mindestens 1 Tipp mit Quote < 1.80 auf Heim
        ist_heim_favorit = False
        hat_torschuetze = False
        for t in spiel_tipps:
            quote = t.get('quote') or 0
            try:
                quote = float(quote)
            except (TypeError, ValueError):
                quote = 0
            markt = (t.get('markt') or '').lower()
            heim = (spiel.get('heim') or '').lower()
            if quote < 1.80 and heim and heim in markt and ('sieg' in markt or 'oder unentschieden' in markt):
                ist_heim_favorit = True
            if any(k in markt for k in ('trifft', 'torschuetz', 'doppelpack', 'hattrick')) and 'punkte' not in markt:
                hat_torschuetze = True
        if ist_heim_favorit and not hat_torschuetze:
            fehlende_torschuetzen_spiele.append(f"{spiel.get('heim')} - {spiel.get('gast')}")
    if fehlende_torschuetzen_spiele:
        print(f"  Pre-Push-Quality WARN: {len(fehlende_torschuetzen_spiele)} Heim-Favorit-Spiel(e) "
              f"OHNE Torschuetzen-Tipp: {fehlende_torschuetzen_spiele[:3]}{'...' if len(fehlende_torschuetzen_spiele)>3 else ''}")


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
        import re
        for bein in k.get('beine', []):
            remap(bein, BEIN_RENAMES)
            # auswahl in markt mergen wenn vorhanden
            if bein.get('auswahl') and not bein.get('markt'):
                bein['markt'] = bein['auswahl']
                bein.pop('auswahl', None)

            # Bein-Pick auf den Original-Tipp-Markt ersetzen.
            # Routine schreibt oft generic "1X2", "Spread", "Doppelte Chance", "Total" -
            # der User sieht dann "Pistons - Magic G7: Spread" ohne zu wissen WELCHE Spread.
            # Wir loesen via tipp_id auf und nehmen den Original-Tipp-Markt-String
            # ("Pistons -7.5 (Spread)", "Borussia Dortmund Sieg", "Beide Teams treffen JA").
            bein_tid = bein.get('tipp_id') or bein.get('id')
            bein_sid = bein.get('spiel_id')
            original_pick = None
            if bein_tid and bein_sid:
                for spiel in d.get('spiele', []):
                    if spiel.get('id') == bein_sid:
                        for t in spiel.get('tipps', []):
                            if t.get('id') == bein_tid or t.get('tipp_id') == bein_tid:
                                original_pick = t.get('markt')
                                break
                        # Match-Titel aus spiel-Daten konstruieren als Fallback
                        if not bein.get('spiel_titel'):
                            heim = spiel.get('heim', '')
                            gast = spiel.get('gast', '')
                            if heim and gast:
                                bein['spiel_titel'] = f"{heim} - {gast}"
                        break

            # Match-Info ins markt-Feld einbauen damit app.js es zeigt (split via ':')
            if bein.get('spiel_titel'):
                titel = bein['spiel_titel']
                clean_titel = re.sub(r'\s*\([^)]*\)\s*$', '', titel).strip()
                if original_pick:
                    # Original-Tipp-Markt nutzen statt generic Routine-String
                    bein['markt'] = f"{clean_titel}: {original_pick}"
                else:
                    cur_markt = bein.get('markt', '')
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

    # Markt-Bluter-Filter: SAFE/VALUE-Tipps auf statistisch verbluteten Markt-Typen werden
    # automatisch auf wackel degradiert. Die Liste kommt aus data/markt_bluter.json,
    # auto-generiert von scripts/statistik_berechnen.py (analog Beobachtungs-Liga).
    # Damit wird Lessons-Anwendung mechanisch erzwungen.
    validate_markt_bluter(d)

    # NBA-Playoff-Haerter (Hebel B 04.05. ROI-Sanierung):
    # 1. Alle NBA-Playoff-Spiele: SAFE -> VALUE (Varianz zu hoch fuer SAFE-Niveau).
    # 2. Decider (G5/G6/G7) + Sieg/Spread/Total: SAFE/VALUE -> WACKEL.
    # Vor SAFE-Confirm laufen lassen, weil B1 erst safe->value, danach hat C nichts mehr
    # zu downgraden.
    validate_nba_playoff(d)

    # SAFE-Confirm-Filter (Hebel C 04.05. -> entschaerft 08.05. nach User-Feedback):
    # Vorher: SAFE -> VALUE wenn Liga nicht in liga_goldgruben (zu hart, kastrierte
    # alle BL/Ligue1/Serie-A SAFEs). Jetzt: SAFE -> VALUE nur bei aktiven
    # Negativ-Signalen (Liga in beobachtungs_ligen, Markt in markt_bluter, oder
    # Quote >1.65 ohne Goldgrube-Kompensation).
    validate_safe_confirm(d)

    # Halluzinations-Schutz fuer Torschuetzen-Tipps (08.05. nach Hojlund-Bug):
    # Tipps auf Spielertor benoetigen Vereins-Verifikations-URL in quellen[]
    # (transfermarkt/kicker/espn/bundesliga player-Seite). Sonst max wackel.
    validate_torschuetze_quelle(d)

    # Recherche-File-Validators (NEU 08.05. Pipeline-Architektur):
    # Wenn data/recherche/<datum>.json existiert (von Recherche-Cloud-Routine 3h vor
    # Tipps-Slot geschrieben), dann pruefen wir Pipeline-Konsistenz:
    # - validate_recherche_completeness: Spiele im Tipps-File muessen im Recherche-File sein
    # - validate_spieler_squad_match: Torschuetzen-Tipps muessen Spieler im Squad haben,
    #   Position-Check (DM/IV/TW als Sturm-Tipp = Downgrade)
    # Bootstrap-tolerant: wenn Recherche-File fehlt, kein Drop - nur Logging.
    validate_recherche_completeness(d)
    validate_spieler_squad_match(d)

    # Saison-Kontext-Sanity (Hebel S 04.05. ROI-Sanierung):
    # Lehre BMG-BVB + Freiburg-Wolfsburg 03.05.: Routine recherchiert saison_kontext{}
    # korrekt, ignoriert ihn dann bei Kategorie-Vergabe. Mapper degradiert SAFE/VALUE
    # auf Sieg/DC/Spread eine Stufe runter wenn Komfort-Pattern (uneinholbar, gerettet),
    # Asymmetrie-Warnung (rotiert, edge kleiner als) oder Belastungs-Pattern (mude,
    # ermuedung) im Block stehen.
    validate_saison_kontext_sanity(d)

    # Markt-Mix-Pflicht (Hebel M 04.05. ROI-Sanierung):
    # Lehre St.Pauli-Mainz 03.05.: Routine packte 3 defensive Tipps (Unter, DC, BTTS-NEIN)
    # auf ein Spiel das der Auswaerts-Underdog 1:2 gewann. (1) Max 1 DC pro Spiel,
    # restliche DC-Tipps gedroppt. (2) Wenn Spiel kein Sieg- und kein Torschuetzen-Tipp
    # hat (rein defensives Set), wird SAFE-DC auf VALUE degradiert - kein offensives
    # Edge-Signal = kein SAFE.
    validate_markt_mix(d)

    # Pre-Push-Quality-Check (Hebel Q 04.05.): ganzheitlicher Dossier-Check.
    # Warnt vor zu hoher DC-Inflation, fehlenden Torschuetzen bei Heim-Favoriten,
    # zu wenig offensive Tipps. Mapper droppt nichts hier - nur Logging fuer User
    # + Routine soll beim naechsten Lauf nachbessern.
    validate_dossier_quality(d)

    # === User-Review v23 (Chelsea-Forest 1:3 Lehrbuch-Fall) ===
    # HR2: Anti-Heim-Bias bei Form-Realitaet. Heim-Sieg/-DC/-Top-Stuermer-Tipps
    # werden auf wackel gedroppt wenn saison_kontext Heim-Krise/Pleiten-Serie/
    # Sturm-Krise erwaehnt.
    validate_heim_form(d)

    # HR3: Joker-Stuermer bei UEFA-Doppelbelastung. Top-Stuermer-Torschuetzen-Tipps
    # bei UEFA-Spiel <4 Tage + Rotation erwartet -> max WACKEL. Routine soll
    # Backup-Stuermer (Quote 3.5+) als VALUE setzen.
    validate_doppelbelastung_joker(d)

    # HR4: Story-Konflikt-Check v2. Scannt begruendung[] auf konkrete Konflikt-Tokens
    # (Heim-Krise bei Heim-Sieg-Tipp, Rotation bei Top-Stuermer-Tipp, Komfort bei SAFE).
    validate_story_konflikt_v2(d)

    # HR6: Auswaerts-Form-Auto-VALUE-Detektor. Warnt wenn Gast-Team Form-Edge hat
    # aber kein Auswaerts-VALUE-Tipp gesetzt wurde (Mapper kann nicht hinzufuegen,
    # nur warnen + Routine beim naechsten Lauf nachbessern).
    validate_auswaerts_auto_value(d)

    # Beobachtungs-Liga-Filter (NEU 04.05. ROI-Sanierung): Tipps aus Beobachtungs-Ligen
    # (z.B. 2.BL, Serie A) werden HARTCODED aus einzeltipps[] und Safe/Balance/Risiko-Kombis
    # gedroppt. Moonshot ab Quote 5x erlaubt. Routine-Prompt-Anweisung allein hat nicht
    # gehalten - 04.05. zeigte 2.BL noch -40% ROI bei 5 Tipps trotz Beobachtungs-Status.
    validate_beobachtungs_liga(d)

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

    # Layer-3-Diversifikation (HR23 08.05.): Sieg-Outcome max 1 Kombi - hartes Drop
    # bei Verstoss; Markt-entkoppelte Doppelungen nur WARN.
    validate_layer3(d)

    # Gesamtquote final berechnen + rechnung fuellen.
    # Muss als allerletztes laufen, weil alle Validators darueber Beine droppen koennen.
    finalize_kombi_quoten(d)

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
