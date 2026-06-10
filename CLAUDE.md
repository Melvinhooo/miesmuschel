# CLAUDE.md — Regeln für das Projekt "Magische Miesmuschel"

> **Entwurf von Claude — bitte vom User finalisieren.**
> Diese Datei beschreibt die verbindlichen Regeln. Änderungen am Design, an der Sprache oder an den Wett-Regeln nur hier — nicht im Code implizit.

---

## Projekt-Zweck

Privates Hobby-Tool für **bet365 DE** zur strukturierten Vorbereitung von Wett-Tagen.

**Aktive Sportarten (Stand 10.06.2026):**
- **Fußball — WM 2026** (USA/Kanada/Mexiko, 11.06.–19.07.2026, 48 Teams, 104 Spiele): jedes einzelne Spiel wird analysiert
- **Fußball — Vereine** (Bundesliga, Premier League, LaLiga, Serie A, DFB-Pokal, Champions League, Europa League, Conference League, Coppa Italia): **Saison-Pause** bis August 2026 — keine Tipps bis Liga-Wiederbeginn
- **Basketball — NBA Finals 2026:** Best-of-7-Serie läuft (Knicks–Spurs), ca. 3 Spiele restlich

Das Tool ist **keine Einnahmequelle**. Jede Version enthält einen Spielerschutz-Hinweis (BZgA-Nummer: 0800 1372700).

---

## Design (unverändert lassen)

- **Hintergrund-Gradient (Tiefsee):** `#001f3f` → `#003d6b` → `#0074b3` (von oben nach unten)
- **Schriften:** `Fraunces` für Headlines/Serifen, `JetBrains Mono` für Body
- **Akzent-Farben:**
  - Lila: `#9c27b0`
  - Rosa: `#e89dd6`
  - Gold: `#ffd700`
  - Himmelblau-hell: `#8fb4d8`
- **Bewertungs-Farben:**
  - SAFE (grün): `#3ec98a` → `#2a9e6a`
  - VALUE (gold/orange): `#ffd700` → `#ff9800`
  - WACKEL (orange/rot): `#ffa94d` → `#e84545`
  - RISIKO (rot/lila): `#e84545` → `#9c27b0`
  - MOONSHOT (lila/rosa/gold Regenbogen): `#9c27b0` → `#e89dd6` → `#ffd700`
- **Animationen:** schwebende Muschel (`float`), aufsteigende Bubbles
- **Logo:** 🐚 (Muschel-Emoji)

---

## Bewertungs-System (verbindlich)

| Label       | Bedeutung                                     | Faire Hit-Rate |
|-------------|-----------------------------------------------|----------------|
| **SAFE**    | Fast ne Garantie, sollte immer reinkommen     | ~75–90 %       |
| **VALUE**   | Quote höher als faire Wahrscheinlichkeit      | 50–70 %        |
| **WACKEL**  | Kann-muss-nicht, spürbares Risiko mit Gründen | 40–55 %        |
| **RISIKO**  | Kombi-Basis, klar spekulativ                  | < 40 %         |
| **MOONSHOT**| Lotterie, Spaßeinsatz                         | < 5 %          |

Reihenfolge in jeder Sektion: **SAFE → VALUE → WACKEL → RISIKO → MOONSHOT**

---

## Einsatz-Limits + Kasse-Stufen-Modell (immer einhalten, im Dossier sichtbar machen)

**Aktuelle Kasse: siehe `data/kasse.json`** (Stand 04.05.2026: **550€**, Basis-Ziel 1000€). Bei Änderung dort zentral updaten — Routinen lesen das File vor jedem Lauf, bestimmen die aktuelle Stufe und rechnen konkrete Euro-Beträge in `begruendung` aus.

### Stufe 1 — Aufbau-Phase (Kasse < 1000€)
Konservativ. Bei 550€-Stand ist das die aktive Stufe.
- **Einzeltipps:** 1–2 % → 5,50–11€
- **Wackel-Einzel:** 0,5 % → 2,75€
- **Kombi Safe ~3x:** 2 % → 11€
- **Kombi Balance ~6–10x:** 0,8 % → 4,40€
- **Kombi Risiko ~15–30x:** 0,25 % → 1,40€
- **Moonshot 300x+:** 0,1 % → 0,55€ (oder 1–2€ Spaßeinsatz)

### Stufe 2 — Profit-Skim (Kasse ≥ 1000€)
**Voraussetzung**: rolling 30-Tage-ROI > +5 % laut `data/statistik.json`. Sonst bleibt Stufe 1 aktiv egal wie hoch die Kasse — Aggressivität ohne Edge ist Selbstmord.

- **Einzeltipps SAFE/VALUE:** 3–5 % bei Quoten 1.80–2.30 (Half-Kelly bei ~60 % Hitrate). Bei 1000€ Kasse: 30–50€. Ziel 100€-Tipps wenn Kasse Richtung 2000€+ wächst.
- **Wackel-Einzel:** 1 % → 10€
- **Kombi-Limits gleich wie Stufe 1** (Kombis bleiben konservativ)

### Auszahlungs-Strategie (Profit-Skim)
- Bei Kasse ≥ Basis + 200€ → **200€ auszahlen**, Kasse zurück auf Basis
- Beispiel: Basis 1000€, bei Stand 1200€ → 200€ raus → neue Kasse 1000€
- Sichert echten Gewinn statt "Papier-Profit im Konto rumdümpelt"

---

## bet365-spezifische Sonderregeln

### 2:0-Insurance-Regel (WICHTIG bei Auswertung)
- Bei einem **direkten Sieg-Tipp** (1X2 / Moneyline) auf Mannschaft X gilt der Tipp als **gewonnen**, sobald X im Spiel mind. **2:0** in Führung lag.
- Egal was danach passiert — auch bei 4:3-Niederlage am Ende, der Tipp ist durch.
- **Gilt NUR für:** 1. Bundesliga + Champions League + **WM 2026** (FIFA-Aktionsregel laut bet365 DE, Stand 10.06.2026 — bei Wechsel bet365-AGB nochmal verifizieren)
- **Gilt NUR für:** direkter Sieg-Tipp (Heim oder Gast)
- **Gilt NICHT für:** Doppelte Chance, Handicap, Über/Unter, BTTS, Genaues Ergebnis, Halbzeit-Wetten
- Bei Auswertung: wenn Halbzeitstand **2:0+ für Sieg-Tipp-Team** UND Endstand zeigt Niederlage → Status `gewonnen` mit Kommentar `"2:0-Insurance"`.

### Einwechslungs-Boost bei Torschützen-Tipps (WICHTIG bei Auswertung)
- Bei Torschützen-Tipps („Spieler X trifft", „Doppelpack X", „Hattrick X") zählen Tore des **direkten Ersatzspielers nach Auswechslung von X** zum Tipp dazu.
- **Beispiel:** Fabio Silva (Dortmund) als Torschütze getippt → in 60. Min ausgewechselt für Guirassy → Guirassy trifft → der Tipp **„Silva trifft" gilt als gewonnen**.
- **Bei Doppelpack/Hattrick:** Tore von X + Tore seines Ersatzes werden **summiert**. Beispiel: X trifft 1×, wird ausgewechselt, Y trifft 2× → für „X Hattrick" gewonnen.
- **Bei Auswertung:** wenn Torschützen-Tipp auf X = noch offen, prüfen:
  1. Wurde X im Spiel ausgewechselt? Wer kam rein?
  2. Hat der Ersatzspieler nach Einwechslung getroffen?
  3. Wenn ja → Status `gewonnen` mit Kommentar `"Einwechslungs-Boost: Tor von [Ersatz] zählt für [X]"`
- **Gilt für:** alle Torschützen-Märkte bei bet365 (Erster, Jederzeit, Letzter, Doppelpack, Hattrick, 2+ Tore, 3+ Tore)
- Praktische Implikation: **Volumen-Stürmer von Mannschaften mit Backup-Stürmer-Qualität sind dadurch sicherer als die nominale Quote suggeriert.**

---

## WM 2026 Sonderregeln (seit 10.06.2026)

WM 2026 läuft 11.06.–19.07.2026 in USA/Kanada/Mexiko. 48 Teams, 12 Gruppen à 4 Teams, neue 32er-K.O.-Runde + Achtelfinale. **Jedes einzelne Spiel wird analysiert** (104 Spiele über 5,5 Wochen).

### Turnier-Phasen + Markt-Tendenzen
- **Gruppenphase (11.–27.06.):** Spiele 1–2 oft taktisch, Spiel 3 (Stichtag) entscheidet Achtelfinal-Quali → hohes Außenseiter-Edge wenn beide schon weiter sind oder einer all-in-must-win
- **Achtelfinale → Viertelfinale (28.06.–11.07.):** K.O.-Modus, Tor-Total tendiert niedriger (Über 2.5 schwerer), Verlängerung möglich → Sieg-Tipps haben 90min-Risiko
- **Halbfinale + Finale (14.–19.07.):** Maximaler Druck, Star-Status entscheidend, Form-Edge nahezu null (alle 100%)

### Spielort-Faktor (Pflicht in saison_kontext)
- **Mexiko-Stadt (Höhe 2.240m):** kontaktscheue Spiele, Tempo niedriger → Über-Tore-Tipps Vorsicht
- **Mexiko-City + Guadalajara:** Hitze + Höhe Doppelbelastung
- **Florida (Miami/Orlando):** hohe Luftfeuchtigkeit, Spät-Spiele besser
- **Kanada (Toronto/Vancouver):** moderates Klima, neutral
- **Kalifornien (LA/SF):** Küsten-Klima, neutral
- **Texas (Dallas/Houston):** Hitze tagsüber

### Vereins-Saison-Müdigkeit
- Spieler aus PL/LaLiga/Serie A spielten 38+ Liga-Spiele + Cup + ggf. CL-Finale 31.05.
- Nur ~10 Tage Pause zwischen Vereinssaison-Ende und WM-Start → Müdigkeits-Risiko bei intensiv eingesetzten Stamm-Spielern
- Bei Pre-WM-Test-Spielen geprüft: wer hat gespielt + wie? (Indiz für Form)

### Squad-Recherche bei Nationalteams
- **WM-Kader:** 26 Spieler pro Team (FIFA-Regel 2022/2026)
- Quellen: FIFA.com/de/tournaments/mens/worldcup/canadamexicousa2026, kicker.de WM-Bereich, transfermarkt.de Nationalmannschaft-Profile, ESPN World Cup, Sky Sports
- Position aus Vereins-Saison auf Nationalmannschaft übertragbar (selten Position-Wechsel)

### Markt-Boykotts WM-spezifisch (Saison-Start)
- **Halbzeit-Endstand-Kombi NIE** (zu unzuverlässig in K.O.)
- **Genaues Ergebnis NIE** (Lotterie, bei K.O. + Verlängerung extra fragwürdig)
- **Erster Torschütze** kritisch — Außenseiter ohne Pre-WM-Daten = WACKEL max

---

## Rechtlich (bet365 DE — Stand 2026)

### Erlaubt
- **Fußball:** 1X2, Doppelte Chance, Handicap (auch Asian), Über/Unter Tore, Beide Teams treffen, Halbzeit-Wetten, HZ/ES-Kombi, Genaues Ergebnis, Torschützen (Erster/Jederzeit/Letzter), Kombi-Konfigurator
- **Basketball:** Moneyline, Spread/Handicap, Über/Unter Punkte (Spiel + Viertel + Halbzeit), Spieler-Punkte, Double-Double, Triple-Double, Meiste Punkte im Spiel, Serien-Wetten, Quartal-Wetten

### Verboten in DE (NIE empfehlen)
- Einzel-Assists, Einzel-Rebounds, Einzel-Steals, Einzel-Blocks, Einzel-Turnovers
- **PRA-Kombos** (Points+Rebounds+Assists o. Ä.)
- Punkte+Assists oder Punkte+Rebounds Kombi-Stats
- Einzelne 3er-Würfe

---

## Saison-Kontext-Pflicht-Analyse (für jeden Tipp)

Vor JEDEM Tipp **diese 4 Faktoren** für beide Mannschaften prüfen + in `begruendung` einfließen lassen:

1. **Parallele Wettbewerbe:** Spielt das Team in dieser Woche noch CL / EL / Conference League / Pokal-HF? → Rotations-Risiko bei Stammspielern
2. **Saisonziel + Tabellenposition:**
   - Meisterschaft / CL-Quali / EL-Quali / Conference-Quali / Klassenerhalt / Abstieg / „nur Spielbetrieb"
3. **Motivations-Asymmetrie:**
   - Wenn Team A noch Saisonziel hat (z.B. Klassenerhalt) und Team B nichts mehr (gerettet, Tabellen-Mittelfeld) → Team A meist Edge
   - Champions können rotieren — Underdogs nutzen das
4. **Recovery / Belastungs-Stand:**
   - Wie viele Tage seit letztem Spiel?
   - CL/EL/Pokal-Spiel diese Woche? → Müdigkeit
   - Verletzungs-Druck im Kader?

**Beispiel:** Mainz @ ~12.0 vs Bayern (25.04.) wäre VALUE gewesen, weil Bayern CL-Doppelbelastung + Mainz im Klassenerhalt-Modus. Plus 2:0-Insurance hätte ausgezahlt (HZ 3:0).

### Mechanisch erzwungen via `saison_kontext{}`-Pflichtfeld

Jedes Spiel im Tipps-JSON muss ein `saison_kontext`-Objekt mit allen 7 Feldern + `quellen[]` (≥1 URL) enthalten:
- `parallel_heim`, `parallel_gast` (paralleler Wettbewerb dieser Woche oder "keine")
- `saisonziel_heim`, `saisonziel_gast` (Platz, Pkt, Saisonziel)
- `motivations_asymmetrie` (1-Satz-Synthese)
- `recovery_heim`, `recovery_gast` (Tage seit letztem Spiel + Belastung)
- `quellen[]` (URLs aus WebSearch/WebFetch — bei Erwähnung von CL/EL/Conference/Pokal MUSS eine Verband-URL dabei sein, sonst Tipps-Downgrade)

**Reference-Implementation:** Spiel `2026-05-03-fre-wol` in `data/tipps/2026-05-03.json` zeigt das vollständig ausgefüllte Format.

**Schema-Mapper-Verhalten** (`.github/scripts/fix_schema.py`, Funktion `validate_saison_kontext`):
- **Hard-Mode (Default):** bei FAIL werden alle `tipps[]` des Spiels gedroppt (einzeltipps + kombis automatisch via valid_refs entfernt). Bei WARN_QUELLE werden SAFE/VALUE auf wackel degradiert. Recherche ist nicht optional.
- **Soft-Mode** (Env `MIESMUSCHEL_KONTEXT_MODE=soft`): nur Logging, Tipps bleiben sichtbar. Nur für Bootstrap/Migration einer Datei.

PWA zeigt rote Box "🔍 Recherche unvollständig" bei FAIL, gelbe Box "⚠️ Quelle fehlt" bei WARN_QUELLE direkt unter dem Spielheader.

---

## Tonalität

- **Deutsche Sprache** überall. Keine englischen Wett-Begriffe ("over/under", "moneyline" usw.) außer wenn es in DE Standard ist.
- **Ehrlich**: wenn eine Kombi keine 100x erreicht, das offen sagen.
- **Coinflip-Spiele** markieren und zum Überspringen empfehlen.
- **Quoten** immer mit "bei bet365 live prüfen" — können sich ändern.
- **Locker aber nicht aufgedreht**: nicht "Der Jackpot ruft!", eher "sollte man mitnehmen".

---

## Auto-Markt-Filter (Whitelist + Blacklist, seit 03.05.2026)

`scripts/statistik_berechnen.py` erzeugt zwei Listen aus `nach_markt_typ`-Aggregat:

- **`data/markt_bluter.json`**: Markt-Typen mit ROI < -25 % ODER (Hitrate < 40 % + ROI < -10 %) bei n ≥ 5 Tipps. Schema-Mapper (`fix_schema.py`) **degradiert** SAFE/VALUE-Tipps auf diesen Markt-Typen automatisch auf wackel. Routine MUSS diese Markt-Typen **NIE** als SAFE/VALUE setzen — Mapper greift sonst sowieso.
- **`data/markt_goldgruben.json`**: Markt-Typen mit ROI > +15 % ODER (Hitrate > 75 % + ROI > 0) bei n ≥ 5 Tipps. Tipps-Routine soll diese **aktiv suchen** und priorisieren.

Markt-Typ-Aggregation per Pattern-Matching (`markt_typ()` in `statistik_berechnen.py`): "Real Madrid DC X2", "Bayern DC X2" usw. werden zusammengeführt zu "Doppelte Chance X2". Damit haben wir genug Tipps pro Typ für stabile Statistik.

**Aktuelle Goldgruben (Stand 03.05.):** Doppelte Chance 1X (84.6 % / +9.5 %), Doppelte Chance X2 (77.8 % / +9.4 %), Unter 2.5 Tore (66.7 % / +27.5 %), Torschützen Jederzeit (50 % / +24.4 %). Aktiv suchen.

---

## Auswertung & Volle Spiel-Analyse (seit 03.05.2026)

Die Auswertungs-Routinen schreiben pro Spiel zusätzlich zum bestehenden `ergebnis{}` und `tipps_ergebnis[]` einen Block `volle_analyse{}` mit:

- `halbzeit_stand`, `endstand`
- `tore[]` mit Minute + Schütze + Stand_danach pro Tor
- `drehung{war_drehung, details}` — Algorithmus: Differenz zwischenzeitlich ≥ 2 Tore, Endstand andere Seite gewinnt/Remis
- `markt_resultate{btts, ueber_1_5/2_5/3_5/..., halbzeit_endstand, kein_team_zu_null, ...}`
- `rotation_highlights[]`, `einwechslungs_tor_highlights[]` (wenn Top-Spiele oder Tipp-Bezug)
- `auffaellige_patterns[]` (1-3 Sätze Synthese)

Lessons-Generierung scant nicht nur Tipp-Treffer, sondern auch `volle_analyse[]` über alle Spiele — Drehungs-Cluster, Markt-Pattern aus nicht-getippten Spielen, Rotation-Pattern, Einwechslungs-Boost-Trigger ohne Tipp.

**Reference-Implementation:** `data/ergebnisse/2026-05-02.json`, Spiele `2026-05-02-bay-hei` (Drehung) und `2026-05-02-new-bri` (kein-Drehung-Vergleich).

---

## Ehrlichkeits-Prinzipien

- Jede Kombi-Gesamtquote wird **nachgerechnet**.
- Wenn das Tool einen Spieler in v13 als SAFE empfahl und in v22 als VALUE, Inkonsistenz sichtbar machen und fixen.
- **Lessons Learned** werden im Dossier sichtbar ausgewiesen (nicht heimlich angewandt).
- Bei Tipps mit kleiner Datenbasis (< 10 Beobachtungen): Historie-Hinweis nicht nutzen, Standard-Analyse.

---

## Technische Leitplanken

- **Kein externes JS-Framework**, kein npm — Vanilla JavaScript
- **Python-Scripts:** nur `requests` als Extra-Bibliothek erlaubt, Rest Standard-Library
- **Keine Browser-Storage-APIs** (localStorage / sessionStorage) — alle persistenten Daten liegen in `/data/` als JSON
- **Fetch-Problematik:** Dateien werden per Doppelklick geöffnet (`file://`) — darum `statistik.js` statt `statistik.json` (Script-Include statt fetch)
- **Neue Sections** im bestehenden Stil bauen (`.tip-card`, `.box`, `.game-card` wiederverwenden)

---

## Datenstruktur

Drei Dossier-Typen, **identisches Schema**, unterschiedliches Zeitfenster.

- **Tipp-Tag:** `/data/tipps/YYYY-MM-DD.json` — generiert Mo-Fr 16:00 + Sa-So 11:30
- **Tipp-Wochenende:** `/data/tipps_wochenende/YYYY-MM-DD.json` — Anker = Samstag, generiert Donnerstag 18:00 als Vorschau auf Sa+So
- **Tipp-Woche:** `/data/tipps_woche/YYYY-MM-DD.json` — Anker = Montag der Ziel-Woche, generiert Sonntag 18:00 als Vorschau für die kommende Mo-So-Woche
- **Ergebnis-Tag:** `/data/ergebnisse/YYYY-MM-DD.json` (gleiche Struktur, Ergebnisse gefüllt)
- **Lessons:** `/data/lessons.json`
- **Statistik:** `/data/statistik.js` (Script-Datei, setzt `window.__MIESMUSCHEL_STAT`)
- **API-Keys:** `/data/config.json` (NICHT committen, steht in `.gitignore`)

Auto-generierte JS-Wrapper (vom GitHub-Action erzeugt nach jedem Push):
- `data/tipps.js` → `window.__MIESMUSCHEL_TIPPS`
- `data/tipps_wochenende.js` → `window.__MIESMUSCHEL_TIPPS_WOCHENENDE`
- `data/tipps_woche.js` → `window.__MIESMUSCHEL_TIPPS_WOCHE`

Alle drei Dossier-Typen verwenden identische Pflicht-Felder (datum, hinweis, spiele[], einzeltipps[], kombis[], lessons_angewandt[], footer) und identische Hartregeln (max 5 Tipps/Spiel, Layer-1 + Layer-2 Diversifikation, Reality-Check via statistik.json).

---

## Workflow

1. **Claude erstellt Dossier** im Chat → schreibt `data/tipps/YYYY-MM-DD.json`
2. **User spielt Tipps** bei bet365 (oder nicht)
3. **Nächster Tag:** User doppelklickt `scripts/ergebnisse_holen.bat`
   → Python holt Ergebnisse via API
   → schreibt `data/ergebnisse/YYYY-MM-DD.json`
   → ruft `statistik_berechnen.py` auf → schreibt `data/statistik.js`
4. **User öffnet `index.html`** → Tab "📊 Historie" zeigt aktualisierte Kennzahlen
5. **Claude liest vor nächstem Dossier** alle Ergebnis-Dateien + `lessons.json` → passt Empfehlungen an

---

## Archivierungs-Regeln

- Alte `magische-miesmuschel-vXX.html` nach `/archiv/` verschieben, **nicht löschen**
- `index.html` ist immer die aktuelle App
- Wenn CLAUDE neue Dossier-Version erstellt, alte als `archiv/index-YYYY-MM-DD.html` sichern

---

## Spielerschutz (immer im Footer)

> 18+ · bet365 DE · Hobby-Wetten
> Sucht-Hilfe BZgA: **0800 1372700**
> Hobby-Tool. Keine Einkommensquelle. Nur setzen was du verlieren kannst. Stress → Pause. Probleme → Hilfe holen.
