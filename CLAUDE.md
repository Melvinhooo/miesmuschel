# CLAUDE.md — Regeln für das Projekt "Magische Miesmuschel"

> **Entwurf von Claude — bitte vom User finalisieren.**
> Diese Datei beschreibt die verbindlichen Regeln. Änderungen am Design, an der Sprache oder an den Wett-Regeln nur hier — nicht im Code implizit.

---

## Projekt-Zweck

Privates Hobby-Tool für **bet365 DE** zur strukturierten Vorbereitung von Wett-Tagen.
Sportarten: **Fußball** (Bundesliga, Premier League, LaLiga, Serie A, DFB-Pokal, Champions League, Coppa Italia) und **Basketball** (NBA).

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

## Einsatz-Limits (immer einhalten, im Dossier sichtbar machen)

- **Einzeltipps:** 1–2 % der Kasse
- **Kombi ~50–100x:** max. 0,5 %
- **Kombi ~250x:** max. 0,25 %
- **Lotterie 1000x+:** max. 0,1 % — besser 1–2 € Spaßeinsatz

---

## bet365-spezifische Sonderregeln

### 2:0-Insurance-Regel (WICHTIG bei Auswertung)
- Bei einem **direkten Sieg-Tipp** (1X2 / Moneyline) auf Mannschaft X gilt der Tipp als **gewonnen**, sobald X im Spiel mind. **2:0** in Führung lag.
- Egal was danach passiert — auch bei 4:3-Niederlage am Ende, der Tipp ist durch.
- **Gilt NUR für:** 1. Bundesliga + Champions League
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

---

## Tonalität

- **Deutsche Sprache** überall. Keine englischen Wett-Begriffe ("over/under", "moneyline" usw.) außer wenn es in DE Standard ist.
- **Ehrlich**: wenn eine Kombi keine 100x erreicht, das offen sagen.
- **Coinflip-Spiele** markieren und zum Überspringen empfehlen.
- **Quoten** immer mit "bei bet365 live prüfen" — können sich ändern.
- **Locker aber nicht aufgedreht**: nicht "Der Jackpot ruft!", eher "sollte man mitnehmen".

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
