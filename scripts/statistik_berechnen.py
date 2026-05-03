"""Aggregiert alle Dateien in data/ergebnisse/ zu data/statistik.js (+ .json).

Rechnet:
- Trefferquote:    gewonnen / (gewonnen + verloren)    — pushes und offene rausgerechnet
- ROI in Prozent:  Netto-Gewinn / Summe-Einsatz * 100  — alle Tipps mit Einheits-Einsatz (1 Unit)
- Zeitfenster:     letzte 30 Tage / letzte 90 Tage / gesamt
- Aufschluesselung: nach Liga, Markt, Quoten-Range, Kategorie

Schreibt:
  data/statistik.json    (maschinen-lesbar)
  data/statistik.js      (Script-Tag-fertig fuer die App)
  data/lessons.js        (gerendert aus data/lessons.json)

Aufruf:
  python statistik_berechnen.py

Wird auch vom ergebnisse_holen.py am Ende automatisch aufgerufen.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


# =========================================================================
# Pfade
# =========================================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_ERG       = ROOT / "data" / "ergebnisse"
DATA_LES_JSON  = ROOT / "data" / "lessons.json"
DATA_STAT_JSON = ROOT / "data" / "statistik.json"
DATA_STAT_JS   = ROOT / "data" / "statistik.js"
DATA_LES_JS    = ROOT / "data" / "lessons.js"
DATA_BEOB_JSON     = ROOT / "data" / "beobachtungs_ligen.json"
DATA_BLUTER_JSON   = ROOT / "data" / "markt_bluter.json"
DATA_GOLDGRUBEN_JSON = ROOT / "data" / "markt_goldgruben.json"

# Beobachtungs-Liga-Schwellen
BEOB_MIN_TIPPS = 4
BEOB_MAX_ROI   = -30.0   # ROI schlechter als -30% -> Beobachtung
BEOB_EXIT_ROI  = -10.0   # ROI besser als -10% -> raus aus Beobachtung
POKAL_MARKER   = ("pokal", "cup", "copa", "coppa", "coupe")

# Markt-Bluter-Schwellen (auto-generated Blacklist)
BLUTER_MIN_TIPPS = 5
BLUTER_MAX_ROI   = -25.0   # ROI schlechter als -25% bei n>=5 -> Bluter
BLUTER_MAX_HITRATE = 40.0  # Trefferquote unter 40% -> Bluter
# Markt-Goldgruben-Schwellen (auto-generated Whitelist)
GOLDGRUBE_MIN_TIPPS = 5
GOLDGRUBE_MIN_ROI    = 15.0   # ROI besser als +15% bei n>=5 -> Goldgrube
GOLDGRUBE_MIN_HITRATE = 75.0  # Trefferquote ueber 75% -> Goldgrube


# =========================================================================
# Hilfsfunktionen
# =========================================================================

def markt_typ(markt: str) -> str:
    """Aggregiert spielspezifische Markt-Strings (z.B. 'Real Madrid DC X2') auf den
    generischen Markt-Typ ('Doppelte Chance'). Damit sammeln sich genug Tipps pro Typ
    fuer Bluter/Goldgruben-Erkennung. Wenn das Pattern-Matching kein Match findet,
    bleibt die Funktion bei der Original-Marktbezeichnung (so verhalten wir uns nicht
    aggressiver als noetig).
    """
    if not markt:
        return "Sonstige"
    m = markt.lower()
    # Doppelte Chance (sehr eindeutig)
    if "doppelte chance" in m or " dc " in f" {m} " or " dc-" in m:
        if "(1x)" in m or " 1x" in m: return "Doppelte Chance 1X"
        if "(x2)" in m or " x2" in m: return "Doppelte Chance X2"
        if "(12)" in m: return "Doppelte Chance 12"
        return "Doppelte Chance"
    # BTTS
    if "beide teams treffen" in m or "btts" in m:
        if " ja" in m or "(ja)" in m: return "Beide Teams treffen JA"
        if " nein" in m or "(nein)" in m: return "Beide Teams treffen NEIN"
        return "Beide Teams treffen"
    # Torschuetzen (NICHT mit Punkte verwechseln)
    if ("trifft" in m or "torschuetz" in m or "jederzeit tor" in m or "tor (jederzeit)" in m) and "punkte" not in m:
        if "doppelpack" in m: return "Torschuetzen Doppelpack"
        if "hattrick" in m: return "Torschuetzen Hattrick"
        if "erster" in m: return "Torschuetzen Erster"
        return "Torschuetzen Jederzeit"
    # Tor-Maerkte (Ueber/Unter Tore)
    if "tore" in m or " tor " in f" {m} ":
        if "mehr als" in m or "ueber" in m or "über" in m or "ueb. " in m or "ueb " in m:
            return f"Ueber {extract_zahl(m)} Tore"
        if "weniger als" in m or "unter" in m or "unt. " in m:
            return f"Unter {extract_zahl(m)} Tore"
    # NBA Player-Punkte
    if "punkte" in m and any(name_token in m for name_token in (" ", "-")):
        # Spielerpunkte - hat einen Spielernamen + "Mehr/Ueber X.5 Punkte"
        if "mehr als" in m or "ueber" in m or "über" in m:
            # Player-Pkt-Linien sind sehr individuell, alle zusammenfassen
            return "Spieler-Punkte Ueber (NBA)"
        if "weniger als" in m or "unter" in m:
            return "Spieler-Punkte Unter (NBA)"
        if "double-double" in m or "dd" in m: return "Double-Double (NBA)"
        if "triple-double" in m or "td" in m: return "Triple-Double (NBA)"
    # NBA Total (Spielsumme Punkte)
    if ("punkte gesamt" in m or "punkte (total)" in m or "(total)" in m or "total" in m and "punkte" in m):
        if "ueber" in m or "über" in m or "mehr als" in m:
            return "Total Ueber (NBA)"
        if "unter" in m or "weniger als" in m:
            return "Total Unter (NBA)"
    # Spread/Handicap
    if "spread" in m or "handicap" in m or "(spread)" in m:
        return "Spread/Handicap"
    # Direkter Sieg (1X2 / Moneyline)
    if "moneyline" in m or "(ml)" in m or "(1x2)" in m or "1x2" in m or m.endswith(" sieg") or " sieg " in f" {m} ":
        return "Sieg (1X2 / ML)"
    # 1.HZ Sieger
    if "1.hz" in m or "halbzeit-sieger" in m or "hz sieger" in m or "fuehrt zur halbzeit" in m:
        return "1.HZ Sieger"
    return markt  # Fallback: Original-Markt (kein Aggregat)


def extract_zahl(s: str) -> str:
    """Extrahiert die erste X.5-Zahl aus einem Markt-String."""
    import re
    m = re.search(r"(\d+\.5)", s)
    return m.group(1) if m else "?"


def quoten_range(q: float) -> str:
    """Packt eine Quote in einen Bucket."""
    if q < 1.50: return "1.00-1.50"
    if q < 2.00: return "1.50-2.00"
    if q < 3.00: return "2.00-3.00"
    return "3.00+"


def make_group() -> dict:
    """Leerer Zaehler-Container."""
    return {
        "tipps": 0, "gewonnen": 0, "verloren": 0, "push": 0, "offen": 0,
        "einsatz": 0.0, "netto": 0.0,
        "trefferquote": 0.0, "roi_prozent": 0.0,
    }


def finalize(g: dict) -> dict:
    """Berechnet Trefferquote + ROI aus den Zaehlern."""
    decided = g["gewonnen"] + g["verloren"]
    g["trefferquote"] = round(g["gewonnen"] / decided * 100, 1) if decided else 0.0
    g["roi_prozent"]  = round(g["netto"] / g["einsatz"] * 100, 1) if g["einsatz"] else 0.0
    # Runden fuer Anzeige
    g["netto"]   = round(g["netto"], 2)
    g["einsatz"] = round(g["einsatz"], 2)
    return g


def update_group(g: dict, status: str, gewinn: float) -> None:
    g["tipps"] += 1
    # Einsatz + Netto nur fuer entschiedene Tipps (gewonnen/verloren/push).
    # Offene Tipps sollen den ROI nicht verwaessern.
    if status in ("gewonnen", "verloren", "push"):
        g["einsatz"] += 1.0       # Einheits-Einsatz: 1 Tipp = 1 Unit
        g["netto"]   += gewinn
    if status in g:
        g[status] += 1
    else:
        g["offen"] += 1           # unbekannter Status -> offen


# =========================================================================
# Einträge aus data/ergebnisse/ einsammeln
# =========================================================================

def lade_entries() -> list[dict]:
    """Alle ausgespielten Einzeltipps als Liste Dicts.

    entry = {"datum", "liga", "markt", "quote", "kategorie", "status", "gewinn"}
    """
    entries: list[dict] = []
    if not DATA_ERG.exists():
        return entries

    for pfad in sorted(DATA_ERG.glob("*.json")):
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"   [WARN] {pfad.name}: {exc}")
            continue

        datum = daten.get("datum") or pfad.stem
        spiele_nach_id = {s["id"]: s for s in daten.get("spiele", []) if s.get("id")}

        # 1) Einzeltipps-Liste (vom User / Claude abgegebene Picks)
        einzel = daten.get("einzeltipps_ergebnis") or daten.get("einzeltipps") or []
        for et in einzel:
            spiel = spiele_nach_id.get(et.get("spiel_id"))
            if not spiel:
                continue
            tipp = next((t for t in spiel.get("tipps", []) if t.get("id") == et.get("tipp_id")), None)
            if not tipp:
                continue
            erg_eintrag = next(
                (e for e in spiel.get("tipps_ergebnis", [])
                 if e.get("tipp_id") == et.get("tipp_id")),
                None,
            )
            status = (erg_eintrag or {}).get("status") or et.get("status") or "offen"
            gewinn = float((erg_eintrag or {}).get("gewinn_faktor") or 0.0)
            clv = (erg_eintrag or {}).get("clv_prozent")
            try:
                clv_val = float(clv) if clv is not None else None
            except (ValueError, TypeError):
                clv_val = None
            entries.append({
                "datum":     datum,
                "liga":      spiel.get("liga", "?"),
                "markt":     tipp.get("markt", "?"),
                "quote":     float(tipp.get("quote") or 0.0),
                "kategorie": (tipp.get("kategorie") or "?").lower(),
                "status":    status,
                "gewinn":    gewinn,
                "clv":       clv_val,
            })
    return entries


def berechne_beobachtungs_ligen(entries: list[dict], ab_datum: str) -> list[dict]:
    """Findet Ligen mit rolling 30d ROI < BEOB_MAX_ROI bei mind. BEOB_MIN_TIPPS Tipps.
    Pokale werden ausgeschlossen.
    """
    by_liga: dict[str, dict] = {}
    for e in entries:
        if e["datum"] < ab_datum:
            continue
        liga = e["liga"] or "?"
        if liga not in by_liga:
            by_liga[liga] = make_group()
        update_group(by_liga[liga], e["status"], e["gewinn"])

    beobachtung: list[dict] = []
    for liga, g in by_liga.items():
        finalize(g)
        if any(p in liga.lower() for p in POKAL_MARKER):
            continue
        if g["tipps"] >= BEOB_MIN_TIPPS and g["roi_prozent"] < BEOB_MAX_ROI:
            beobachtung.append({
                "liga":              liga,
                "tipps_30d":         g["tipps"],
                "roi_30d_prozent":   g["roi_prozent"],
                "trefferquote_30d":  g["trefferquote"],
                "netto_30d":         g["netto"],
            })
    return sorted(beobachtung, key=lambda x: x["roi_30d_prozent"])


def berechne_markt_bluter(by_markt: dict[str, dict]) -> list[dict]:
    """Findet Bluter-Maerkte (Hitrate ODER ROI klar negativ).

    Auto-Blacklist die der Schema-Mapper liest und Tipps auf diesen Maerkten
    hart auf wackel degradiert. Damit wird die Lesson-Anwendung mechanisch erzwungen.

    Kriterien (OR-Verknuepfung, n>=BLUTER_MIN_TIPPS):
    - ROI < BLUTER_MAX_ROI (-25%): klar geld-negativer Markt
    - Trefferquote < BLUTER_MAX_HITRATE (40%) UND ROI < -10%: klar treffer-negativer Markt
    """
    bluter = []
    for markt, g in by_markt.items():
        if g["tipps"] < BLUTER_MIN_TIPPS:
            continue
        ist_roi_bluter = g["roi_prozent"] < BLUTER_MAX_ROI
        ist_hit_bluter = g["trefferquote"] < BLUTER_MAX_HITRATE and g["roi_prozent"] < -10.0
        if ist_roi_bluter or ist_hit_bluter:
            bluter.append({
                "markt":         markt,
                "tipps":         g["tipps"],
                "trefferquote":  g["trefferquote"],
                "roi_prozent":   g["roi_prozent"],
                "netto":         g["netto"],
            })
    return sorted(bluter, key=lambda x: x["roi_prozent"])


def berechne_markt_goldgruben(by_markt: dict[str, dict]) -> list[dict]:
    """Findet Goldgrube-Maerkte (Hitrate ODER ROI klar positiv).

    Auto-Whitelist die Tipps-Routinen aktiv suchen sollen.

    Kriterien (OR-Verknuepfung, n>=GOLDGRUBE_MIN_TIPPS):
    - ROI > GOLDGRUBE_MIN_ROI (+15%): klar geld-positiver Markt
    - Trefferquote > GOLDGRUBE_MIN_HITRATE (75%) UND ROI > 0: klar treffer-positiver Markt
    """
    goldgruben = []
    for markt, g in by_markt.items():
        if g["tipps"] < GOLDGRUBE_MIN_TIPPS:
            continue
        ist_roi_gold = g["roi_prozent"] > GOLDGRUBE_MIN_ROI
        ist_hit_gold = g["trefferquote"] > GOLDGRUBE_MIN_HITRATE and g["roi_prozent"] > 0
        if ist_roi_gold or ist_hit_gold:
            goldgruben.append({
                "markt":         markt,
                "tipps":         g["tipps"],
                "trefferquote":  g["trefferquote"],
                "roi_prozent":   g["roi_prozent"],
                "netto":         g["netto"],
            })
    return sorted(goldgruben, key=lambda x: -x["roi_prozent"])


def clv_aggregat(entries: list[dict], ab_datum: str | None = None) -> dict:
    """Aggregiert CLV-Werte ueber alle Tipps mit clv-Wert."""
    werte: list[float] = []
    by_liga: dict[str, list[float]] = {}
    for e in entries:
        if ab_datum and e["datum"] < ab_datum:
            continue
        if e.get("clv") is None:
            continue
        werte.append(e["clv"])
        liga = e["liga"] or "?"
        by_liga.setdefault(liga, []).append(e["clv"])

    def stats(vals: list[float]) -> dict:
        if not vals:
            return {"n": 0, "durchschnitt": 0.0, "median": 0.0}
        s = sorted(vals)
        n = len(s)
        med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        return {
            "n":             n,
            "durchschnitt":  round(sum(vals) / len(vals), 2),
            "median":        round(med, 2),
        }

    return {
        "gesamt":    stats(werte),
        "nach_liga": {liga: stats(vals) for liga, vals in by_liga.items()},
    }


# =========================================================================
# Aggregation
# =========================================================================

def baue_tages_verlauf() -> list[dict]:
    """Liest alle data/ergebnisse/*.json und baut pro Tag eine Detail-Sicht fuer den
    Historie-Tab: pro Spiel die Einzeltipps mit Markt + Quote + Kategorie + Status +
    Kommentar + Endstand. Damit kann der User klick-fuer-klick zurueckschauen.

    Resultat-Struktur:
    [
      {"datum": "2026-05-02", "gesamt": {...}, "spiele": [
         {"heim":"X", "gast":"Y", "liga":"BL", "endstand":"3:3",
          "tipps": [{"markt":"X Sieg", "quote":1.18, "kategorie":"safe",
                    "status":"verloren", "kommentar":"3:3", "gewinn_faktor":-1.0}]
         }
      ]}, ...
    ]
    Sortiert nach Datum absteigend (juengste zuerst).
    """
    verlauf = []
    if not DATA_ERG.exists():
        return verlauf
    for pfad in sorted(DATA_ERG.glob("*.json"), reverse=True):
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        datum = daten.get("datum") or pfad.stem
        einzel_ids = set()
        for et in daten.get("einzeltipps", []) or daten.get("einzeltipps_ergebnis", []):
            tid = et.get("tipp_id") or et.get("id")
            if tid:
                einzel_ids.add(tid)

        gesamt = make_group()
        spiele_view = []
        for spiel in daten.get("spiele", []):
            tipps_view = []
            tipps_ergebnis = {te.get("tipp_id"): te for te in spiel.get("tipps_ergebnis", [])}
            for tipp in spiel.get("tipps", []):
                tid = tipp.get("id")
                if tid not in einzel_ids:
                    continue  # Nur Einzeltipps zeigen, nicht alle Markt-Optionen
                te = tipps_ergebnis.get(tid, {})
                status = te.get("status", "offen")
                gewinn = float(te.get("gewinn_faktor") or 0.0)
                update_group(gesamt, status, gewinn)
                tipps_view.append({
                    "markt":      tipp.get("markt"),
                    "quote":      float(tipp.get("quote") or tipp.get("quote_bet365") or 0.0),
                    "kategorie":  (tipp.get("kategorie") or "").lower(),
                    "status":     status,
                    "gewinn_faktor": gewinn,
                    "kommentar":  te.get("kommentar", ""),
                })
            if tipps_view:
                spiele_view.append({
                    "id":       spiel.get("id"),
                    "liga":     spiel.get("liga"),
                    "heim":     spiel.get("heim"),
                    "gast":     spiel.get("gast"),
                    "endstand": (spiel.get("ergebnis") or {}).get("endstand", "—"),
                    "tipps":    tipps_view,
                })
        # Kombis-Sicht: pro Kombi-Schein die Beine + Status anzeigen
        kombis_view = []
        kombis_ergebnis = {ke.get("kombi_id"): ke for ke in daten.get("kombis_ergebnis", [])}
        for kombi in daten.get("kombis", []):
            ke = kombis_ergebnis.get(kombi.get("id"), {})
            beine_view = []
            for bein in kombi.get("beine", []):
                # Pro Bein das Tipp-Ergebnis aus dem zugehoerigen Spiel finden
                bein_status = "offen"
                bein_kommentar = ""
                bein_sid = bein.get("spiel_id")
                bein_tid = bein.get("tipp_id") or bein.get("id")
                if bein_sid and bein_tid:
                    for spiel in daten.get("spiele", []):
                        if spiel.get("id") == bein_sid:
                            for te in spiel.get("tipps_ergebnis", []):
                                if te.get("tipp_id") == bein_tid:
                                    bein_status = te.get("status", "offen")
                                    bein_kommentar = te.get("kommentar", "")
                                    break
                            break
                beine_view.append({
                    "markt":     bein.get("markt"),
                    "quote":     float(bein.get("quote") or 0.0),
                    "status":    bein_status,
                    "kommentar": bein_kommentar,
                })
            # Kombi-Status: gewonnen wenn alle Beine gewonnen, sonst verloren wenn eins verloren, sonst offen
            statuses = [b["status"] for b in beine_view]
            if all(s == "gewonnen" for s in statuses) and statuses:
                kombi_status = "gewonnen"
            elif any(s == "verloren" for s in statuses):
                kombi_status = "verloren"
            elif statuses:
                kombi_status = "offen"
            else:
                kombi_status = "offen"
            kombis_view.append({
                "name":            kombi.get("name", kombi.get("id", "?")),
                "kategorie":       (kombi.get("kategorie") or "").lower(),
                "gesamtquote":     float(kombi.get("gesamtquote") or 0.0),
                "einsatz_prozent": float(kombi.get("empfohlener_einsatz_prozent") or 0.0),
                "status":          kombi_status,
                "beine":           beine_view,
            })

        if spiele_view or kombis_view:
            finalize(gesamt)
            verlauf.append({
                "datum":  datum,
                "gesamt": gesamt,
                "spiele": spiele_view,
                "kombis": kombis_view,
            })
    return verlauf


def aggregiere(entries: list[dict], ab_datum: str | None = None) -> dict:
    """Liefert alle Aggregate fuer den gefilterten Zeitraum."""
    gesamt = make_group()
    by_liga:      dict[str, dict] = {}
    by_markt:     dict[str, dict] = {}
    by_markt_typ: dict[str, dict] = {}
    by_range:     dict[str, dict] = {}
    by_kat:       dict[str, dict] = {}

    for e in entries:
        if ab_datum and e["datum"] < ab_datum:
            continue

        update_group(gesamt, e["status"], e["gewinn"])

        for zielmap, key in (
            (by_liga,      e["liga"] or "?"),
            (by_markt,     e["markt"] or "?"),
            (by_markt_typ, markt_typ(e["markt"] or "?")),
            (by_range,     quoten_range(e["quote"])),
            (by_kat,       e["kategorie"] or "?"),
        ):
            if key not in zielmap:
                zielmap[key] = make_group()
            update_group(zielmap[key], e["status"], e["gewinn"])

    finalize(gesamt)
    for zielmap in (by_liga, by_markt, by_markt_typ, by_range, by_kat):
        for k in zielmap:
            finalize(zielmap[k])

    return {
        "gesamt":            gesamt,
        "nach_liga":         by_liga,
        "nach_markt":        by_markt,
        "nach_markt_typ":    by_markt_typ,
        "nach_quoten_range": by_range,
        "nach_kategorie":    by_kat,
    }


# =========================================================================
# Hauptprogramm
# =========================================================================

def main() -> int:
    entries = lade_entries()
    heute   = datetime.now().date()
    c30     = (heute - timedelta(days=30)).isoformat()
    c90     = (heute - timedelta(days=90)).isoformat()

    gesamt_agg = aggregiere(entries)
    agg_30     = aggregiere(entries, c30)
    agg_90     = aggregiere(entries, c90)

    clv_gesamt = clv_aggregat(entries)
    clv_30d    = clv_aggregat(entries, c30)

    stat = {
        "letzte_berechnung": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "gesamt":            gesamt_agg["gesamt"],
        "letzte_30_tage":    agg_30["gesamt"],
        "letzte_90_tage":    agg_90["gesamt"],
        "nach_liga":         gesamt_agg["nach_liga"],
        "nach_markt":        gesamt_agg["nach_markt"],
        "nach_markt_typ":    gesamt_agg["nach_markt_typ"],
        "nach_quoten_range": gesamt_agg["nach_quoten_range"],
        "nach_kategorie":    gesamt_agg["nach_kategorie"],
        "clv_gesamt":        clv_gesamt,
        "clv_30_tage":       clv_30d,
        "tages_verlauf":     baue_tages_verlauf(),
    }

    # Beobachtungs-Liga-Liste schreiben (separates File, von Tipps-Routinen gelesen)
    beob_ligen = berechne_beobachtungs_ligen(entries, c30)
    beob_payload = {
        "stand":                datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "kriterium":            f"rolling 30 Tage ROI < {BEOB_MAX_ROI}% bei min. {BEOB_MIN_TIPPS} Tipps",
        "ausstiegs_kriterium":  f"rolling 30 Tage ROI > {BEOB_EXIT_ROI}% -> Liga wieder voll bespielbar",
        "ligen":                beob_ligen,
    }
    DATA_BEOB_JSON.write_text(
        json.dumps(beob_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Auto-generierte Markt-Blacklist + Whitelist (gelesen von fix_schema.py + Routinen).
    # Lehre: Lessons beachten reicht nicht — Maerkte mit klarer Bilanz werden mechanisch
    # gefiltert (Bluter) bzw. priorisiert (Goldgruben).
    # Aggregation auf markt_typ - alle "DC X2"-Tipps zusammen, alle "BTTS Ja" zusammen, etc.
    # Damit haben wir ueberhaupt n>=5 pro Markt-Typ. nach_markt-Eintraege sind oft nur 1-2 Tipps,
    # weil sie spielspezifisch sind ("Real Madrid DC X2" != "Bayern DC X2").
    bluter = berechne_markt_bluter(gesamt_agg["nach_markt_typ"])
    goldgruben = berechne_markt_goldgruben(gesamt_agg["nach_markt_typ"])
    DATA_BLUTER_JSON.write_text(
        json.dumps({
            "stand":     datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "kriterium": f"Hitrate < {BLUTER_MAX_HITRATE}% UND ROI < {BLUTER_MAX_ROI}% bei min. {BLUTER_MIN_TIPPS} Tipps",
            "wirkung":   "Schema-Mapper degradiert SAFE/VALUE auf wackel + entfernt aus einzeltipps[]/Hauptkombis (analog Beobachtungs-Liga).",
            "maerkte":   bluter,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DATA_GOLDGRUBEN_JSON.write_text(
        json.dumps({
            "stand":     datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "kriterium": f"Hitrate > {GOLDGRUBE_MIN_HITRATE}% UND ROI > {GOLDGRUBE_MIN_ROI}% bei min. {GOLDGRUBE_MIN_TIPPS} Tipps",
            "wirkung":   "Tipps-Routinen sollen diese Maerkte aktiv suchen. Schema-Mapper warnt wenn Spiel im Dossier ist und der Markt nicht als Tipp gesetzt wurde.",
            "maerkte":   goldgruben,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Rohdaten (maschinen-lesbar)
    DATA_STAT_JSON.write_text(
        json.dumps(stat, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # App-friendly (Script-Tag-fertig, umgeht fetch-auf-file-Problem)
    DATA_STAT_JS.write_text(
        "// Automatisch erzeugt von scripts/statistik_berechnen.py — bitte nicht von Hand editieren.\n"
        "window.__MIESMUSCHEL_STAT = "
        + json.dumps(stat, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )

    # Lessons mit-rendern (JSON -> JS)
    if DATA_LES_JSON.exists():
        try:
            lessons = json.loads(DATA_LES_JSON.read_text(encoding="utf-8"))
            DATA_LES_JS.write_text(
                "// Automatisch erzeugt aus data/lessons.json.\n"
                "window.__MIESMUSCHEL_LESSONS = "
                + json.dumps(lessons, ensure_ascii=False, indent=2)
                + ";\n",
                encoding="utf-8",
            )
        except json.JSONDecodeError as exc:
            print(f"   [WARN] lessons.json kaputt: {exc}")

    print(f"[ok] {len(entries)} Einzeltipps ausgewertet")
    print(f"     -> {DATA_STAT_JSON}")
    print(f"     -> {DATA_STAT_JS}")
    print(f"     -> {DATA_LES_JS}")
    print(f"     -> {DATA_BEOB_JSON} ({len(beob_ligen)} Beobachtungs-Liga(s))")
    print(f"     -> {DATA_BLUTER_JSON} ({len(bluter)} Markt-Bluter)")
    print(f"     -> {DATA_GOLDGRUBEN_JSON} ({len(goldgruben)} Markt-Goldgrube(n))")
    if entries:
        g = stat["gesamt"]
        print(f"     Gesamt: {g['tipps']} Tipps, Trefferquote {g['trefferquote']}%, ROI {g['roi_prozent']:+.1f}%")
        if clv_gesamt["gesamt"]["n"] > 0:
            print(f"     CLV (n={clv_gesamt['gesamt']['n']}): Durchschnitt {clv_gesamt['gesamt']['durchschnitt']:+.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
