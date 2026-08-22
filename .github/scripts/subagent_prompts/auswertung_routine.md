# Auswertungs-Routine — Master-Prompt

> Gilt für `miesmuschel-auswertung-daily` (täglich 08:00 Berlin) und den `miesmuschel-auswertung-watchdog` (09:00). Die Cloud-Prompts sind seit 22.08.2026 nur noch schlanke Wrapper — **diese Datei ist die Quelle der Wahrheit**.

## Auftrag

Auswertung von gestern: Ergebnisse holen, offene Tipps schließen, **volle Spiel-Analyse** pro Spiel, CLV, Lessons, Statistik + Beobachtungs-Ligen aktualisieren, pushen.

**Keine neuen Tipps generieren.** Bei Fehlern in Python/Git: kein Push.

## Ablauf

### 1. Setup-Read (parallel)
`CLAUDE.md`, `data/lessons.json`, `data/statistik.json`, `data/beobachtungs_ligen.json`, `data/kader_wechsel_2026.json`.

### 2. Datum
`GESTERN = TZ=Europe/Berlin date -d "yesterday" +%Y-%m-%d`

### 3. Existenz-Checks
- `data/tipps/$GESTERN.json` fehlt → sauber beenden, kein Push.
- `data/ergebnisse/$GESTERN.json` bereits komplett (inkl. `volle_analyse` pro Spiel) → Schritte 4–5 überspringen.

### 4. Ergebnisse holen
```bash
python3 scripts/ergebnisse_holen.py $GESTERN
```

### 5. Offene Tipps per WebSearch ergänzen (parallel pro offenem Tipp)

**A) Torschützen:** `"[Heim] vs [Gast] Torschuetzen [Datum]"` + `"Auswechslungen [Datum]"`.

> **bet365-Einwechslungs-Boost (PFLICHT):** hat der getippte Spieler X nicht getroffen, wurde aber **selbst ausgewechselt**, und sein Ersatz Y trifft danach → `status="gewonnen"`, `kommentar="Einwechslungs-Boost: Tor von Y zaehlt fuer X"`. Der Boost greift **nur**, wenn X selbst runter ging. Bei Doppelpack/Hattrick werden die Tore von X und Y summiert.

**B) NBA-Spieler-Punkte:** `"NBA [Team] [Datum] box score"`. (Offseason bis ~Oktober 2026 — normalerweise nichts zu tun.)

**C) Pokal-Wettbewerbe** (DFB-Pokal, Coppa, FA Cup — nicht im football-data-Free-Tier): `"[Heim] vs [Gast] Endstand"`.

### 5a. Sonderregeln, die regelmäßig falsch ausgewertet werden

**2:0-Insurance** — gilt **nur**:
- bei **direkten Sieg-Tipps** (1X2 / Moneyline), und
- **nur in 1. Bundesliga und Champions League**.

Nicht bei Supercup, DFB-Pokal, Europa/Conference League, 2. Bundesliga, ausländischen Ligen. Nicht bei Doppelter Chance, Handicap, Über/Unter, BTTS, Genauem Ergebnis, Halbzeit-Wetten.
Trifft sie zu (Team lag mit 2+ Toren vorn, verliert am Ende): `status="gewonnen"`, `kommentar="2:0-Insurance"`.

**Elfmeterschießen** (Supercups, Pokal-K.-o., Finals): 1X2- und DC-Märkte werten **nur die regulären 90 Minuten**. Ein Remis nach 90 Minuten ist für die Wette ein Remis — unabhängig davon, wer den Titel holt. Bei Verlängerung gilt dasselbe: 90 Minuten zählen.

### 5b. Volle Spiel-Analyse pro Spiel (PFLICHT)

Für **jedes** Spiel im Ergebnis-File ein `volle_analyse{}`-Block direkt nach `tipps_ergebnis[]`.
Referenz: `data/ergebnisse/2026-05-02.json`, Spiele `2026-05-02-bay-hei` (Drehung) und `2026-05-02-new-bri` (Gegenbeispiel).

Recherche pro Spiel (WebSearches parallel in einem Block):
- Halbzeitstand (football-data-Antwort oder `"[Heim] vs [Gast] Halbzeitstand [Datum]"`)
- Tor-Verteilung mit Schütze + Minute (`kicker.de` / `sofascore` / ESPN)
- NBA: Viertel-Stände

```json
"volle_analyse": {
  "halbzeit_stand": "1:2",
  "endstand": "3:3",
  "tore": [
    {"min": 22, "team": "gast", "spieler": "Zivzivadze", "stand_danach": "0:1"}
  ],
  "drehung": {"war_drehung": true, "details": "..."},
  "markt_resultate": {
    "btts": "JA",
    "ueber_1_5": true, "ueber_2_5": true, "ueber_3_5": true,
    "halbzeit_endstand": "Heidenheim/Unentschieden",
    "kein_team_zu_null": true
  },
  "rotation_highlights": [{"team": "heim", "spieler": "...", "details": "..."}],
  "einwechslungs_tor_highlights": [{"team": "heim", "ein": "...", "aus": "...", "minute": 65, "tor": true}],
  "auffaellige_patterns": ["1-3 Sätze Synthese"]
}
```

**Drehungs-Algorithmus:** hatte ein Zwischenstand in `tore[]` eine Differenz ≥ 2 Tore, und gewinnt am Ende die andere Seite oder es endet remis → `war_drehung: true`.

**Pflichtfelder:** `halbzeit_stand`, `endstand`, `tore[]`, `drehung{}`, `markt_resultate{}` (mindestens `btts`, `ueber_2_5`, `ueber_3_5`, `halbzeit_endstand`). Bei Datenlücken: `null` setzen. **Nichts erfinden.**

### 6. CLV (best effort, parallel)
Für entschiedene Tipps Closing-Quote holen (WebFetch oddsportal).
`clv_prozent = (opening_quote - closing_quote) / closing_quote * 100`
In `tipps_ergebnis`: `closing_quote`, `clv_prozent`, `clv_quelle`. Nicht verfügbar → alle drei `null`.

### 7. Statistik neu berechnen
```bash
python3 scripts/statistik_berechnen.py
```
Erzeugt auch `data/beobachtungs_ligen.json`, `data/markt_bluter.json`, `data/markt_goldgruben.json`, `data/liga_goldgruben.json`.

### 8. Lessons ziehen (bis zu 4 pro Tag)

Quelle ist **nicht nur** `tipps_ergebnis[]`, sondern alle `volle_analyse[]`-Blöcke — auch von Spielen ohne Tipp.

- **8a) Korrelation** (Pflicht bei Kombi-Verlusten): steckte ein Spiel-Bein in mehreren Kombis?
- **8b) Knappe Verluste:** Beine, die an Mini-Margen scheiterten.
- **8c) Markt-Cluster:** Goldgruben / Bluter aus `statistik.json` (n ≥ 5).
- **8d) Liga-Performance:** ROI-Trends je Liga.
- **8e) Kategorie-Reality:** SAFE-Hitrate gegen Soll 75–90 %.
- **8f) Drehungs-Cluster:** 2+ Drehungen an einem Tag → Vorsicht bei Kurzquoten-Sieg-Tipps.
- **8g) Markt-Pattern aus nicht-getippten Spielen:** z.B. 5/6 Spiele über 2.5 → Über-2.5 als VALUE markieren.
- **8h) Rotations-Pattern:** Top-Team rotiert + Punktverlust → `saison_kontext.parallel_*` schärfen.
- **8i) Einwechslungs-Boost-Trigger ohne Tipp:** Boost wäre gelaufen, aber kein Torschützen-Tipp lag drauf → Volumen-Backup-Stürmer aktiv scannen.

Anhängen an `data/lessons.json` mit `bezug_spiel_id` wo möglich. Max 4/Tag, Mindestbasis 5 Tipps für Markt-Lessons. Mindestens eine Lesson sollte aus 8f–8i kommen, wenn die Daten es hergeben.

Danach nochmal `python3 scripts/statistik_berechnen.py`.

### 8b. Kader- und Trainer-Pflege (Selbstlernen — seit 22.08.2026)

Beim Auswerten fallen Kader-Realitäten auf, die im Tool noch falsch stehen. Das ist der beste Moment, sie festzuhalten.

Wenn dir beim Auswerten auffällt, dass
- ein getippter Spieler gar nicht (mehr) im Kader dieses Vereins steht,
- ein Torschütze für einen Verein trifft, bei dem ihn das Tool nicht führt,
- oder ein anderer Trainer an der Linie stand als angenommen,

dann **ergänze das direkt in `data/kader_wechsel_2026.json`** (`abgaenge_NICHT_mehr_fuer_alten_verein_tippen[]`, `zugaenge_neue_optionen[]`, `trainer_2026_27[]`), mit `quelle`-URL, und setze `stand` auf das heutige Datum. Kurz per WebSearch verifizieren, nicht raten.

Historischer Anlass: Adeyemi wurde noch Wochen nach seinem Wechsel zu Barcelona als Dortmund-Torschütze getippt.

### 9. lessons.js regenerieren
```bash
python3 - <<'PYJS'
import json
data = open('data/lessons.json', 'rb').read().decode('utf-8')
open('data/lessons.js', 'wb').write(
    ('// Automatisch erzeugt aus data/lessons.json.\nwindow.__MIESMUSCHEL_LESSONS = '
     + data + ';\n').encode('utf-8'))
print('OK')
PYJS
```

### 10. Push mit Retry
```bash
git add -A
if git diff --cached --quiet; then echo "PUSHED=0"
else
  git commit -m "Auto-Auswertung $GESTERN + Volle-Analyse + Lessons + CLV"
  git push origin main || (git pull --rebase origin main && git push origin main)
fi
```
`web-push.yml` triggert auf `data/ergebnisse/` und schickt die Auswertungs-Push aufs iPhone.

### 11. Kurz-Report
Bilanz von gestern · wie viele Spiele mit `volle_analyse` · 2:0-Insurance / Einwechslungs-Boost angewandt? · CLV-Anzahl · neue Lessons · Kader-Ergänzungen · URL.
