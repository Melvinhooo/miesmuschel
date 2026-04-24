"""Holt Ergebnisse fuer offene Tipp-Tage aus kostenlosen APIs.

- Fussball: football-data.org v4  (kostenloser Key, Wettbewerbe BL1/PL/PD/SA/CL)
- NBA:      balldontlie.io v1     (kostenloser Key)

Was das Script auswerten KANN (automatisch):
  - 1X2, Doppelte Chance, Handicap
  - Ueber/Unter Tore, Beide Teams treffen
  - NBA Siege, Spread, Ueber/Unter Punkte
  - NBA Spieler-Punkte (Ueber/Unter), Double-Double, Triple-Double

Was das Script NICHT kann (bleibt "offen" -> manuell eintragen):
  - Fussball-Torschuetzen (Free Tier liefert keine Torschuetzen)
  - DFB-Pokal, Coppa Italia (nicht im Free Tier)
  - Genaues Ergebnis mit Verlaengerung/Elfer (wenn Free Tier nur 90-Min-Score gibt)

Aufruf:
  python ergebnisse_holen.py            # verarbeitet alle offenen Tage
  python ergebnisse_holen.py 2026-04-22 # nur diesen Tag

Am Ende ruft das Script statistik_berechnen.py auf.
"""

from __future__ import annotations

import json
import re
import sys
import time
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("[FEHLER] Python-Paket 'requests' fehlt. Installieren mit:")
    print("         pip install requests")
    sys.exit(1)


# =========================================================================
# Pfade & Konfiguration
# =========================================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_TIPPS = ROOT / "data" / "tipps"
DATA_ERG   = ROOT / "data" / "ergebnisse"
CONFIG     = ROOT / "data" / "config.json"

# Football-Data-Wettbewerbscodes (Free Tier)
LIGA_ZU_CODE = {
    "bundesliga":      "BL1",
    "premier league":  "PL",
    "laliga":          "PD",
    "la liga":         "PD",
    "serie a":         "SA",
    "champions league": "CL",
    "ligue 1":         "FL1",
    "eredivisie":      "DED",
    # Wettbewerbe ohne Free-Tier-Abdeckung:
    "dfb-pokal":       None,
    "coppa italia":    None,
    "nba":             "__NBA__",
}


def load_config() -> dict[str, Any]:
    """Liest data/config.json. Toleriert Windows-Doppel-Endung config.json.json."""
    pfad = CONFIG
    if not pfad.exists():
        # Windows-Explorer-Falle: bei versteckten Endungen wird aus
        # "config.json" beim Umbenennen "config.json.json".
        alt = CONFIG.with_suffix(".json.json")
        if alt.exists():
            print(f"[HINWEIS] Datei heisst versehentlich '{alt.name}' (doppelte Endung).")
            print(f"          Benenne sie in Windows um zu 'config.json' — oder ich mach es jetzt.")
            try:
                alt.rename(CONFIG)
                print("          -> umbenannt. Mach weiter.")
                pfad = CONFIG
            except OSError as exc:
                print(f"          umbenennen fehlgeschlagen: {exc}")
                return {}
        else:
            print("[HINWEIS] data/config.json nicht gefunden. Kopiere data/config.example.json")
            print("          zu data/config.json und trag deinen football-data.org-Key ein.")
            return {}
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[FEHLER] config.json ist kein gueltiges JSON: {exc}")
        sys.exit(1)


# =========================================================================
# Hilfsfunktionen
# =========================================================================

def aehnlichkeit(a: str, b: str) -> float:
    """Fuzzy-Score 0..1 fuer Team-Namen-Matching."""
    a = re.sub(r"\b(fc|cf|afc|sc|vfb|vfl|tsg|ssv|1\.|ii|u21|u23)\b", "", a.lower()).strip()
    b = re.sub(r"\b(fc|cf|afc|sc|vfb|vfl|tsg|ssv|1\.|ii|u21|u23)\b", "", b.lower()).strip()
    return SequenceMatcher(None, a, b).ratio()


def beste_zuordnung(ziel_heim: str, ziel_gast: str, kandidaten: list[dict]) -> dict | None:
    """Suche in API-Response das wahrscheinlichste Spiel."""
    best = None
    best_score = 0.0
    for k in kandidaten:
        h = k.get("_home", "")
        a = k.get("_away", "")
        s = (aehnlichkeit(ziel_heim, h) + aehnlichkeit(ziel_gast, a)) / 2
        if s > best_score:
            best_score = s
            best = k
    return best if best_score > 0.6 else None


def parse_datum(anstoss_iso: str) -> str:
    """'2026-04-22T20:45:00+02:00' -> '2026-04-22'."""
    return anstoss_iso.split("T")[0]


# =========================================================================
# Football-Data.org
# =========================================================================

def fetch_fussball_matches(datum: str, liga_code: str, api_key: str) -> list[dict]:
    """Holt alle Matches einer Liga an einem Tag.

    Rueckgabe: Liste Dicts mit _home/_away/_status/_ht_home/_ht_away/_ft_home/_ft_away.
    """
    if not api_key:
        print(f"   [FUSSBALL] kein Key -> {liga_code} wird nicht abgefragt")
        return []
    # football-data.org akzeptiert Date-Range
    url = f"https://api.football-data.org/v4/competitions/{liga_code}/matches"
    params = {"dateFrom": datum, "dateTo": datum}
    try:
        r = requests.get(url, params=params,
                         headers={"X-Auth-Token": api_key}, timeout=10)
    except requests.RequestException as exc:
        print(f"   [FUSSBALL] Netzwerkfehler {liga_code}: {exc}")
        return []
    if r.status_code == 429:
        print(f"   [FUSSBALL] Rate-Limit ({liga_code}) -> 70s warten")
        time.sleep(70)
        return fetch_fussball_matches(datum, liga_code, api_key)
    if r.status_code != 200:
        print(f"   [FUSSBALL] HTTP {r.status_code} bei {liga_code}: {r.text[:200]}")
        return []
    matches = r.json().get("matches", [])
    out = []
    for m in matches:
        ft = (m.get("score") or {}).get("fullTime") or {}
        ht = (m.get("score") or {}).get("halfTime") or {}
        out.append({
            "_home":     (m.get("homeTeam") or {}).get("name", ""),
            "_away":     (m.get("awayTeam") or {}).get("name", ""),
            "_status":   m.get("status", ""),
            "_ft_home":  ft.get("home"),
            "_ft_away":  ft.get("away"),
            "_ht_home":  ht.get("home"),
            "_ht_away":  ht.get("away"),
            "_id":       m.get("id"),
        })
    return out


# =========================================================================
# balldontlie.io (NBA)
# =========================================================================

def fetch_nba_games(datum: str, api_key: str | None) -> list[dict]:
    """Holt NBA-Spiele eines Tages.

    NBA-Spiele nach MEZ ueberschneiden sich mit US-Datum — wir pruefen
    Spiel-Datum +/- 1 Tag.
    """
    urls = []
    base_d = datetime.fromisoformat(datum)
    for delta in (-1, 0):
        d = (base_d + timedelta(days=delta)).strftime("%Y-%m-%d")
        urls.append(d)

    headers = {}
    if api_key:
        headers["Authorization"] = api_key

    all_games: list[dict] = []
    for d in urls:
        url = "https://api.balldontlie.io/v1/games"
        try:
            r = requests.get(url, params={"dates[]": d, "per_page": 100},
                             headers=headers, timeout=10)
        except requests.RequestException as exc:
            print(f"   [NBA] Netzwerkfehler {d}: {exc}")
            continue
        if r.status_code == 401:
            print("   [NBA] 401 Unauthorized -> balldontlie-Key noetig.")
            print("         Kostenlos unter https://www.balldontlie.io/")
            return []
        if r.status_code != 200:
            print(f"   [NBA] HTTP {r.status_code}: {r.text[:200]}")
            continue
        for g in r.json().get("data", []):
            all_games.append({
                "_home":    g.get("home_team", {}).get("full_name", ""),
                "_away":    g.get("visitor_team", {}).get("full_name", ""),
                "_status":  g.get("status", ""),
                "_ft_home": g.get("home_team_score"),
                "_ft_away": g.get("visitor_team_score"),
                "_ht_home": None,
                "_ht_away": None,
                "_id":      g.get("id"),
            })
    return all_games


def fetch_nba_player_stats(game_id: int, api_key: str | None) -> list[dict]:
    """Pro Spieler: punkte, rebounds, assists, etc. Wird fuer Spielerpunkte-Tipps gebraucht."""
    if not game_id:
        return []
    headers = {}
    if api_key:
        headers["Authorization"] = api_key
    url = "https://api.balldontlie.io/v1/stats"
    try:
        r = requests.get(url, params={"game_ids[]": game_id, "per_page": 100},
                         headers=headers, timeout=10)
    except requests.RequestException:
        return []
    if r.status_code != 200:
        return []
    out = []
    for s in r.json().get("data", []):
        p = s.get("player", {})
        out.append({
            "name":    f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
            "punkte":  s.get("pts", 0) or 0,
            "reb":     s.get("reb", 0) or 0,
            "ast":     s.get("ast", 0) or 0,
            "team":    (s.get("team") or {}).get("abbreviation", ""),
        })
    return out


# =========================================================================
# Tipp-Bewertung
# =========================================================================

@dataclass
class Spielergebnis:
    heim_tore: int | None
    gast_tore: int | None
    ht_heim:   int | None
    ht_gast:   int | None
    status:    str  # "FINISHED" / "LIVE" / "SCHEDULED" / ...
    spieler:   list[dict]   # nur NBA relevant

    @property
    def final(self) -> bool:
        return self.status in ("FINISHED", "Final") and self.heim_tore is not None


def bewerte_tipp(tipp: dict, heim_name: str, gast_name: str, erg: Spielergebnis) -> dict:
    """Liefert {"tipp_id", "status", "gewinn_faktor", "kommentar"}.

    status in {"gewonnen", "verloren", "push", "offen"}
    gewinn_faktor: Quote-1 bei gewonnen, -1 bei verloren, 0 bei push/offen
    """
    tipp_id = tipp.get("id")
    quote   = float(tipp.get("quote") or 0)
    markt   = (tipp.get("markt") or "").lower()

    def won():  return {"tipp_id": tipp_id, "status": "gewonnen", "gewinn_faktor": round(quote - 1, 4), "kommentar": ""}
    def lost(): return {"tipp_id": tipp_id, "status": "verloren", "gewinn_faktor": -1.0,              "kommentar": ""}
    def push(): return {"tipp_id": tipp_id, "status": "push",     "gewinn_faktor":  0.0,              "kommentar": ""}
    def offen(k=""): return {"tipp_id": tipp_id, "status": "offen", "gewinn_faktor": 0.0, "kommentar": k or "manuell eintragen"}

    if not erg.final:
        return offen("Spiel laut API noch nicht final")

    h, g = erg.heim_tore, erg.gast_tore
    summe = (h or 0) + (g or 0)

    # 1X2 / Sieg-Tipps
    if "sieg" in markt or "1x2" in markt or markt in ("heimsieg", "auswaertssieg"):
        if heim_name.lower() in markt or "heim" in markt:
            return won() if h > g else lost()
        if gast_name.lower() in markt or "auswaerts" in markt or "gast" in markt:
            return won() if g > h else lost()
        if "unentschieden" in markt or "remis" in markt or markt.strip() == "x":
            return won() if h == g else lost()

    # Doppelte Chance
    if "doppelte chance" in markt or "1x" == markt.strip() or "x2" == markt.strip() or "12" == markt.strip():
        if "1x" in markt or heim_name.lower() in markt:
            return won() if h >= g else lost()
        if "x2" in markt or gast_name.lower() in markt:
            return won() if g >= h else lost()
        if "12" in markt:
            return won() if h != g else lost()

    # Beide Teams treffen
    if "beide" in markt and "treffen" in markt:
        ja_ja = "ja" in markt or "yes" in markt or "nein" not in markt
        both_scored = (h or 0) > 0 and (g or 0) > 0
        return (won() if both_scored else lost()) if ja_ja else (won() if not both_scored else lost())

    # Ueber/Unter Tore (Fussball) oder Gesamtpunkte (Basketball)
    m = re.search(r"(ueber|über|mehr als|more than|over|unter|weniger als|less than|under)\s*(\d+[.,]?\d*)\s*(tore?|punkte? gesamt|total|pts gesamt)", markt)
    if m:
        schwelle = float(m.group(2).replace(",", "."))
        ist_ueber = m.group(1) in ("ueber", "über", "mehr als", "more than", "over")
        if summe == schwelle:
            return push()
        return (won() if summe > schwelle else lost()) if ist_ueber else (won() if summe < schwelle else lost())

    # Handicap — Beispiel: "Bayern -1.5", "Leverkusen +0.5"
    m = re.search(r"([+-]?\d+[.,]?\d*)\s*$", markt)
    if m and ("handicap" in markt or re.search(r"[-+]\d", markt)):
        hc = float(m.group(1).replace(",", "."))
        if heim_name.lower() in markt or "heim" in markt:
            return won() if (h + hc) > g else (push() if (h + hc) == g else lost())
        if gast_name.lower() in markt or "auswaerts" in markt or "gast" in markt:
            return won() if (g + hc) > h else (push() if (g + hc) == h else lost())

    # NBA Spieler-Punkte: "Brown Mehr als 23.5 Punkte", "Tatum ueber 25.5 Pkt"
    m = re.search(r"(?:mehr als|ueber|über|more than|over|unter|weniger als|under|less than)\s*(\d+[.,]?\d*)\s*(?:pkt|punkte|points)", markt)
    if m:
        schwelle = float(m.group(1).replace(",", "."))
        # Spielername aus Markt-String extrahieren (vor dem Zahl/Schwellwert-Teil)
        pre = markt.split(m.group(0))[0].strip()
        ist_ueber = "mehr" in markt or "ueber" in markt or "über" in markt or "more" in markt or "over" in markt
        # Finde besten Spieler-Match
        bester = None
        bester_score = 0.0
        for sp in erg.spieler or []:
            sc = aehnlichkeit(sp["name"], pre)
            if sc > bester_score:
                bester_score = sc
                bester = sp
        if bester_score < 0.6 or not bester:
            return offen(f"Spieler '{pre}' nicht in Statistik gefunden")
        pts = bester["punkte"]
        if pts == schwelle:
            return push()
        return (won() if pts > schwelle else lost()) if ist_ueber else (won() if pts < schwelle else lost())

    # NBA Double-Double / Triple-Double
    if "double-double" in markt or "double double" in markt:
        pre = markt.split("double")[0].strip()
        bester = max(erg.spieler or [], key=lambda sp: aehnlichkeit(sp["name"], pre), default=None)
        if not bester or aehnlichkeit(bester["name"], pre) < 0.6:
            return offen("Spieler nicht in Statistik")
        threshold_count = sum(1 for v in (bester["punkte"], bester["reb"], bester["ast"]) if v >= 10)
        if "triple" in markt:
            return won() if threshold_count >= 3 else lost()
        return won() if threshold_count >= 2 else lost()

    return offen(f"Markt nicht automatisch auswertbar ({tipp.get('markt')})")


# =========================================================================
# Haupt-Loop
# =========================================================================

def liga_code(liga: str) -> str | None:
    """Liga-String -> API-Code. Tolerant gegen Zusaetze wie 'R1 G2', 'Halbfinale' usw."""
    key = (liga or "").strip().lower()
    # Exact Match zuerst
    if key in LIGA_ZU_CODE:
        return LIGA_ZU_CODE[key]
    # Substring-Match fuer Dinge wie "NBA Playoffs R1 G2", "DFB-Pokal Halbfinale"
    for liga_name, code in LIGA_ZU_CODE.items():
        if liga_name in key:
            return code
    # NBA-Sonderfall
    if "nba" in key or "playoff" in key:
        return "__NBA__"
    return "__UNBEKANNT__"


def verarbeite_tag(pfad: Path, config: dict) -> bool:
    """Erzeugt data/ergebnisse/<datum>.json fuer einen Tipp-Tag. True wenn was geschrieben."""
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    datum = daten.get("datum") or pfad.stem
    print(f"\n>> Verarbeite {datum}  ({pfad.name})")

    # API-Caches pro Liga + Datum
    fussball_cache: dict[str, list[dict]] = {}
    nba_cache: list[dict] | None = None
    nba_stats_cache: dict[int, list[dict]] = {}

    alle_offen = True
    for spiel in daten.get("spiele", []):
        liga = spiel.get("liga", "")
        code = liga_code(liga)
        d_an = parse_datum(spiel.get("anstoss", f"{datum}T00:00:00"))

        if code == "__NBA__":
            if nba_cache is None:
                nba_cache = fetch_nba_games(d_an, config.get("balldontlie_key"))
            kandidaten = nba_cache
        elif code is None:
            print(f"   [SKIP] {spiel['id']}: {liga} nicht im Free-Tier -> manuell eintragen")
            spiel["ergebnis"] = None
            spiel["tipps_ergebnis"] = [
                {"tipp_id": t["id"], "status": "offen", "gewinn_faktor": 0.0,
                 "kommentar": f"{liga} nicht im API-Free-Tier"}
                for t in spiel.get("tipps", [])
            ]
            continue
        elif code == "__UNBEKANNT__":
            print(f"   [SKIP] {spiel['id']}: Liga '{liga}' unbekannt")
            continue
        else:
            cache_key = f"{code}|{d_an}"
            if cache_key not in fussball_cache:
                fussball_cache[cache_key] = fetch_fussball_matches(d_an, code, config.get("football_data_key", ""))
                time.sleep(6)  # Free Tier: 10 calls/min -> konservativ 6s Puffer
            kandidaten = fussball_cache[cache_key]

        match = beste_zuordnung(spiel.get("heim", ""), spiel.get("gast", ""), kandidaten)
        if not match:
            print(f"   [OFFEN] {spiel['id']}: kein API-Match gefunden")
            spiel["ergebnis"] = None
            spiel["tipps_ergebnis"] = [
                {"tipp_id": t["id"], "status": "offen", "gewinn_faktor": 0.0,
                 "kommentar": "kein API-Match"}
                for t in spiel.get("tipps", [])
            ]
            continue

        # Spieler-Stats nachladen bei NBA
        spieler = []
        if code == "__NBA__" and match.get("_id"):
            if match["_id"] not in nba_stats_cache:
                nba_stats_cache[match["_id"]] = fetch_nba_player_stats(
                    match["_id"], config.get("balldontlie_key"))
            spieler = nba_stats_cache[match["_id"]]

        erg = Spielergebnis(
            heim_tore=match.get("_ft_home"),
            gast_tore=match.get("_ft_away"),
            ht_heim=match.get("_ht_home"),
            ht_gast=match.get("_ht_away"),
            status=match.get("_status", ""),
            spieler=spieler,
        )

        spiel["ergebnis"] = {
            "heim_tore": erg.heim_tore,
            "gast_tore": erg.gast_tore,
            "halbzeit":  {"heim": erg.ht_heim, "gast": erg.ht_gast} if erg.ht_heim is not None else None,
            "quelle":    "football-data.org" if code != "__NBA__" else "balldontlie.io",
            "abgerufen_am": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        }
        if spieler:
            spiel["ergebnis"]["spieler_stats"] = [
                {"spieler": s["name"], "punkte": s["punkte"], "team": s["team"]}
                for s in spieler if s["punkte"] > 0
            ]

        ergebnisse = [bewerte_tipp(t, spiel.get("heim",""), spiel.get("gast",""), erg) for t in spiel.get("tipps", [])]
        spiel["tipps_ergebnis"] = ergebnisse
        n_gewonnen = sum(1 for e in ergebnisse if e["status"] == "gewonnen")
        n_offen    = sum(1 for e in ergebnisse if e["status"] == "offen")
        if n_offen < len(ergebnisse):
            alle_offen = False
        print(f"   [OK] {spiel['id']}: {erg.heim_tore}:{erg.gast_tore}  -> {n_gewonnen}/{len(ergebnisse)} Tipps gewonnen, {n_offen} offen")

    # Einzeltipps-Auswertung aggregieren
    einzel_erg = []
    tipp_status: dict[tuple, str] = {}
    for spiel in daten.get("spiele", []):
        for e in spiel.get("tipps_ergebnis", []):
            tipp_status[(spiel["id"], e["tipp_id"])] = e["status"]
    for et in daten.get("einzeltipps", []):
        sid = et.get("spiel_id")
        tid = et.get("tipp_id")
        key = (sid, tid)
        einzel_erg.append({**et, "status": tipp_status.get(key, "offen")})
    daten["einzeltipps_ergebnis"] = einzel_erg

    # Kombi-Auswertung (tolerant: beine ohne spiel_id werden ueber tipp_id global gesucht)
    # Baue Index: tipp_id -> status (falls unique ueber alle Spiele)
    tid_status: dict[str, str] = {}
    tid_ambiguous: set[str] = set()
    for (sid, tid), st in tipp_status.items():
        if tid in tid_status and tid_status[tid] != st:
            tid_ambiguous.add(tid)
        tid_status[tid] = st

    def bein_status(b: dict) -> str:
        sid = b.get("spiel_id")
        tid = b.get("tipp_id")
        if sid and tid and (sid, tid) in tipp_status:
            return tipp_status[(sid, tid)]
        if tid and tid in tid_status and tid not in tid_ambiguous:
            return tid_status[tid]
        return "offen"

    kombi_erg = []
    for k in daten.get("kombis", []):
        statuses = [bein_status(b) for b in k.get("beine", k.get("tipps", []))]
        if not statuses or "offen" in statuses:
            st = "offen"
        elif all(s == "gewonnen" for s in statuses):
            st = "gewonnen"
        else:
            st = "verloren"
        kombi_erg.append({"kombi_id": k.get("id"), "status": st, "gesamtquote": k.get("gesamtquote")})
    daten["kombis_ergebnis"] = kombi_erg

    daten["ausgewertet_am"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    DATA_ERG.mkdir(parents=True, exist_ok=True)
    ziel = DATA_ERG / f"{datum}.json"
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   -> geschrieben: {ziel}")
    return not alle_offen


def main() -> int:
    config = load_config()
    if not config.get("football_data_key"):
        print("[WARN] Kein football_data_key gesetzt — Fussball-Spiele werden uebersprungen.")
    if not config.get("balldontlie_key"):
        print("[WARN] Kein balldontlie_key gesetzt — NBA-Spiele werden uebersprungen.")

    # Ziel-Datum aus Argv, sonst alle Tage aus data/tipps/ die noch keine Ergebnisse haben
    wenn_einzel = sys.argv[1] if len(sys.argv) > 1 else None
    if wenn_einzel:
        tage = [DATA_TIPPS / f"{wenn_einzel}.json"]
        if not tage[0].exists():
            print(f"[FEHLER] {tage[0]} existiert nicht.")
            return 1
    else:
        tage = sorted(DATA_TIPPS.glob("*.json"))
        # ueberspringen wenn schon in data/ergebnisse/ und aktuell
        tage = [t for t in tage if not (DATA_ERG / t.name).exists()
                or t.stat().st_mtime > (DATA_ERG / t.name).stat().st_mtime]

    if not tage:
        print("Keine offenen Tipp-Tage.")
    for p in tage:
        try:
            verarbeite_tag(p, config)
        except Exception as exc:   # noqa: BLE001
            print(f"[FEHLER] {p.name}: {exc}")

    # Statistik neu berechnen
    print("\n>> rufe statistik_berechnen.py auf ...")
    stat_script = Path(__file__).with_name("statistik_berechnen.py")
    if stat_script.exists():
        rc = subprocess.call([sys.executable, str(stat_script)])
        return rc
    else:
        print("   (statistik_berechnen.py existiert noch nicht — in Stufe 5)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
