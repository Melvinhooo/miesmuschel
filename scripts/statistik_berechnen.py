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
DATA_BEOB_JSON = ROOT / "data" / "beobachtungs_ligen.json"

# Beobachtungs-Liga-Schwellen
BEOB_MIN_TIPPS = 4
BEOB_MAX_ROI   = -30.0   # ROI schlechter als -30% -> Beobachtung
BEOB_EXIT_ROI  = -10.0   # ROI besser als -10% -> raus aus Beobachtung
POKAL_MARKER   = ("pokal", "cup", "copa", "coppa", "coupe")


# =========================================================================
# Hilfsfunktionen
# =========================================================================

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

def aggregiere(entries: list[dict], ab_datum: str | None = None) -> dict:
    """Liefert alle Aggregate fuer den gefilterten Zeitraum."""
    gesamt = make_group()
    by_liga:  dict[str, dict] = {}
    by_markt: dict[str, dict] = {}
    by_range: dict[str, dict] = {}
    by_kat:   dict[str, dict] = {}

    for e in entries:
        if ab_datum and e["datum"] < ab_datum:
            continue

        update_group(gesamt, e["status"], e["gewinn"])

        for zielmap, key in (
            (by_liga,  e["liga"] or "?"),
            (by_markt, e["markt"] or "?"),
            (by_range, quoten_range(e["quote"])),
            (by_kat,   e["kategorie"] or "?"),
        ):
            if key not in zielmap:
                zielmap[key] = make_group()
            update_group(zielmap[key], e["status"], e["gewinn"])

    finalize(gesamt)
    for zielmap in (by_liga, by_markt, by_range, by_kat):
        for k in zielmap:
            finalize(zielmap[k])

    return {
        "gesamt":            gesamt,
        "nach_liga":         by_liga,
        "nach_markt":        by_markt,
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
        "nach_quoten_range": gesamt_agg["nach_quoten_range"],
        "nach_kategorie":    gesamt_agg["nach_kategorie"],
        "clv_gesamt":        clv_gesamt,
        "clv_30_tage":       clv_30d,
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
    if entries:
        g = stat["gesamt"]
        print(f"     Gesamt: {g['tipps']} Tipps, Trefferquote {g['trefferquote']}%, ROI {g['roi_prozent']:+.1f}%")
        if clv_gesamt["gesamt"]["n"] > 0:
            print(f"     CLV (n={clv_gesamt['gesamt']['n']}): Durchschnitt {clv_gesamt['gesamt']['durchschnitt']:+.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
