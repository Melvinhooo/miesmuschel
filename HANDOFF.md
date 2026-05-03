# 🐚 HANDOFF — Magische Miesmuschel

> **Wenn du neu in diesen Chat kommst: lies dieses Dokument ZUERST.**
> Stand: **02.05.2026 abends** — voll ausgebautes 3-Modus-Tipp-System (Täglich + Wochenende + Woche) mit 12 Cloud-Routinen, Mode-Switcher-PWA, Lern-Loop.

---

## ⚡ TL;DR für den nächsten Claude

**Was läuft komplett autonom (Stand 02.05.):**
- **3 Modi in der App:** 📅 Täglich / 🌊 Wochenende / 📆 Woche — Mode-Pill-Bar oben, gleiche Tab-Nav darunter, Inhalt wechselt je Modus
- **12 Cloud-Routinen** auf Opus 4.7 (Auswertung Mo-Fr + Sa-So eigene, Tagestipps Mo-Fr + Sa-So, Wochenende-Vorschau Do, Wochen-Vorschau So, plus 6 Watchdogs)
- **Push aufs Handy** via GitHub Action (Apple blockt Direkt-Push aus Cloud — Action-Bridge zwingend)
- **Lern-Loop:** Auswertung → Lessons → fließen in alle 3 Tipps-Routinen ein
- **Layer-1+2-Diversifikation** für Kombis (max 1 Bein/Spiel/Kombi + Sieg-Outcome max 1 Kombi)
- **Best-of-Philosophie:** lieber 8-12 sichere Tipps als 25 mittelmäßige

**Performance-Stand:**
- ~85+ Tipps gesamt · Trefferquote ~62% · ROI ~+3-4%
- Beobachtungs-Ligen: **2. Bundesliga** (-40% ROI) + **Serie A** (-32% ROI) → KEINE Tipps in Hauptkombis, nur Moonshot ab 5x

**Memory-Files lesen** (in `~/.claude/projects/.../memory/`):
- `MEMORY.md` — 4 Einträge, Index
- `reference_routines.md` — Alle 12 Routinen, Cron-Zeiten, DST-Hinweis, Push-Subscription
- `feedback_inkrementell_verbessern.md` — STIL BEIBEHALTEN, nur Schwachstellen schärfen
- `feedback_max_5_tipps.md` — Hartlimit gegen Tipps-Inflation
- `feedback_kombi_diversifikation_layer2.md` — Sieg-Outcome max 1 Kombi
- `feedback_keine_extra_kosten.md` — alles im Claude Max + Free Tiers
- `user_ziel_profitabel.md` — Melvi will ernsthaft Profit aus dem Hobby

**Wichtigste KRITISCHE Lessons:**
1. **Cloud-Routinen können stumm sterben bei vielen Spielen** (Stream-Timeout) → Mini-Files-Architektur, aber bei 28+ Spielen reicht's manchmal nicht. Watchdogs als Backup.
2. **Apple blockt Anthropic-Cloud-Push** (HTTP 403) → GitHub Action als Bridge.
3. **`tipp_id` vs `id` Schema-Mapper-Bug** war historisch — gefixt 01.05. Routine schreibt mal so, mal so, Mapper normalisiert auf `id`.
4. **iOS PWA-Service-Worker zickig** — bei UI-Updates Cache-Version bumpen + ggf. PWA neu installieren empfehlen.

---

## 0. Pflicht-Reihenfolge zum Einlesen

1. **Dieses Dokument** — Architektur + Stand
2. **`CLAUDE.md`** — alle Regeln, verbotenen Wettarten, Tonalität
3. **Memory-Files** (siehe oben)
4. **`data/lessons.json`** — alle Wett-Lessons (chronologisch, ~25 Einträge)
5. **`data/beobachtungs_ligen.json`** — aktuelle Liga-Bluter
6. **letzte 3 `data/ergebnisse/*.json`** — aktuelle Form
7. **`data/statistik.json`** — Bilanz inkl. CLV-Aggregation

Dann fragst du Melvi: **"Was steht an?"**

---

## 1. Projekt in einem Satz

Privates Hobby-Tool für **bet365 DE** von **Melvi**: strukturierte Wett-Vorbereitung für Fußball (BL, 2.BL, PL, LaLiga, Serie A, Ligue 1, CL, EL, Conference, nationale Pokale) und NBA. **Hobby, keine Einkommensquelle laut UI** — intern wird aber auf echten Profit hingearbeitet.

---

## 2. Technischer Stack (Stand 02.05.2026)

### Hauptdateien
```
Magische Miesmuschel/
├── index.html                   (App-Schale mit Mode-Pill-Bar oben)
├── assets/
│   ├── styles.css
│   ├── app.js                   (rendert + setMode-Switcher)
│   └── icon.svg
├── manifest.webmanifest
├── sw.js                        (Service Worker v17)
├── data/
│   ├── tipps/YYYY-MM-DD.json              (Tagestipps)
│   ├── tipps_wochenende/YYYY-MM-DD.json    (Anker = Sa der kommenden Woche)
│   ├── tipps_woche/YYYY-MM-DD.json         (Anker = Mo der kommenden Woche)
│   ├── ergebnisse/YYYY-MM-DD.json          (von Auswertungs-Routine)
│   ├── tipps.js                            (auto-generiert → __MIESMUSCHEL_TIPPS)
│   ├── tipps_wochenende.js                 (auto-generiert → __MIESMUSCHEL_TIPPS_WOCHENENDE)
│   ├── tipps_woche.js                      (auto-generiert → __MIESMUSCHEL_TIPPS_WOCHE)
│   ├── lessons.json (+ lessons.js)
│   ├── statistik.json (+ statistik.js)
│   ├── beobachtungs_ligen.json
│   └── config.json                         (API-Keys, GITIGNORED)
├── scripts/
│   ├── ergebnisse_holen.py
│   ├── statistik_berechnen.py
│   └── *.bat
├── .github/
│   ├── workflows/web-push.yml              (4 Pfade-Trigger + Mode-Detection)
│   └── scripts/
│       ├── fix_schema.py                   (Cap + Layer-1 + tipp_id-Fix)
│       └── send_push.py                    (--mode arg: tipps/auswertung/wochenende/woche)
└── archiv/                                 (alte HTML-Versionen)
```

### Externe Services / Stack
| Service | Zweck |
|---|---|
| **GitHub** | Hosting + Version, Repo `Melvinhooo/miesmuschel` public |
| **GitHub Pages** | Live-App https://melvinhooo.github.io/miesmuschel/ |
| **football-data.org** | Fußball-Ergebnisse, Free Tier |
| **balldontlie.io** | NBA-Spiele, Free Tier |
| **Anthropic Cloud Routines** | Autopilot, Max-Plan inklusive |
| **Apple Push Service** | Web-Push aufs iPhone via VAPID |
| **GitHub Actions** | Push-Bridge (Apple blockt Cloud direkt) |

---

## 3. Cloud-Routinen (12 Stück)

### Auswertung
| Name | Trigger-ID | Cron (UTC) | Berlin |
|---|---|---|---|
| `miesmuschel-auswertung-daily` | `trig_01BP9meTHCX6R5mgAJf3QT94` | `30 8 * * 1-5` | Mo-Fr 10:30 |
| `miesmuschel-auswertung-watchdog` | `trig_01Gdq9Ce4nbmqAjdFwdqWZZQ` | `30 9 * * 1-5` | Mo-Fr 11:30 |
| `miesmuschel-auswertung-sa-so` | `trig_01719ftvduk4fqy64prmvEAH` | `30 7 * * 6,0` | Sa+So 09:30 |
| `miesmuschel-auswertung-sa-so-watchdog` | `trig_01UHbhtmtYWbXiyeaJ3HePmG` | `30 8 * * 6,0` | Sa+So 10:30 |

### Tagestipps
| Name | Trigger-ID | Cron (UTC) | Berlin |
|---|---|---|---|
| `miesmuschel-tipps-mo-fr` | `trig_011ps7wgfJwnLX18nUeZV3nu` | `0 14 * * 1-5` | Mo-Fr 16:00 |
| `miesmuschel-watchdog-mo-fr` | `trig_01MSvwzPx9eyUkQahSPZQpzN` | `15 15 * * 1-5` | Mo-Fr 17:15 |
| `miesmuschel-tipps-sa-so` | `trig_01MPfUoxZbHYUA4K6CdQb6G3` | `50 8 * * 6,0` | Sa+So 10:50 |
| `miesmuschel-watchdog-sa-so` | `trig_01HhcexsuWZxeT48au9sLVya` | `50 9 * * 6,0` | Sa+So 11:50 |

### Vorschauen
| Name | Trigger-ID | Cron (UTC) | Berlin |
|---|---|---|---|
| `miesmuschel-tipps-wochenende` | `trig_01XcqwEKXkNoZorUfnSokY5J` | `0 16 * * 4` | Donnerstag 18:00 |
| `miesmuschel-tipps-wochenende-watchdog` | `trig_014N17NrzWynTXgotQ6jaJqP` | `15 17 * * 4` | Donnerstag 19:15 |
| `miesmuschel-tipps-woche` | `trig_017GLjns24ZigL3QqK5qmEPp` | `0 16 * * 0` | Sonntag 18:00 |
| `miesmuschel-tipps-woche-watchdog` | `trig_017Jt5Dg3DYSLCvbKPdEXHL9` | `15 17 * * 0` | Sonntag 19:15 |

### Reminder (One-Shot)
| Name | Trigger-ID | run_once_at | Zweck |
|---|---|---|---|
| `miesmuschel-vorschau-review-reminder` | `trig_016T1CPopa5XWZ5ryJZCQSy9` | `2026-05-18T08:00Z` | 17 Tage nach Vorschau-Einführung: Push "Soll ich Option B (separate Statistiken) bauen?" |

Verwalten via `RemoteTrigger` MCP-Tool oder UI: https://claude.ai/code/routines

### Wochenend-Logik (KRITISCH)
Reihenfolge Sa+So: **Auswertung 09:30 → Watchdog 10:30 → Tipps 10:50 → Tipps-Watchdog 11:50**. So liest die Tipps-Routine immer aktuelle statistik.json + lessons.json.

### Vorschau-Anker-Logik
- Wochenend-Vorschau: `date -d "next Saturday"` für Anker-Datum
- Wochen-Vorschau: `date -d "next Monday"` für Anker
- Robustheit: funktioniert auch bei manuellen Triggers an anderen Wochentagen

### Always-Overwrite (NEU 01.05.)
**Hauptroutinen** (Wochen + Wochenende) haben KEINEN Skip-Guard mehr — sie überschreiben immer die aktuellste Version (z.B. Sonntag 18:00 ersetzt manuelle Probelaufs-Datei mit echten frischen Quoten). **Watchdogs** behalten Skip-Guard (skipt wenn Hauptroutine erfolgreich).

### DST-Anpassung Ende Oktober 2026 PFLICHT
Berlin wechselt MESZ → MEZ am 25.10.2026. Alle 12 Cron-Strings +1h. Details in `reference_routines.md`.

---

## 4. PWA-UI mit Mode-Switcher

### Architektur
```
┌─────────────────────────────────────────┐
│   🐚 Magische Miesmuschel               │
│   Tipp-Dossier YYYY-MM-DD · X Spiele... │
│   🗓️ Wochentag, Datum                   │
└─────────────────────────────────────────┘

  [📅 Täglich] [🌊 Wochenende] [📆 Woche]    ← Mode-Pill-Bar (NEU 01.05.)

  📊 Spiele-Analyse  🎯 Einzeltipps  🚀 Risiko-Kombis  📈 Historie  ℹ️ Regeln
                                                       ↑ Tab-Nav (gleich wie immer)

  [Inhalt der aktiven Section, je nach Modus]
```

### Verhalten
- **Default beim Öffnen:** 📅 Täglich
- **setMode(mode)** schaltet Datensatz: lädt `__MIESMUSCHEL_TIPPS` / `__MIESMUSCHEL_TIPPS_WOCHENENDE` / `__MIESMUSCHEL_TIPPS_WOCHE`, rendert die 3 Sub-Tabs (Spiele/Einzel/Risiko) neu mit Daten des Modus
- **Historie + Regeln** sind modus-übergreifend
- **Empty-State** falls JS-Wrapper noch nicht da: "Wird Donnerstag/Sonntag 18:00 generiert"

### Wichtige UI-Bugs gefixt
- Pill-Bar war zu schmächtig (transparent BG, kleine Schrift, "Wochenende" gestapelt) → fixed mit `flex:1`, padding 13px, blau-getöntem BG, klarem Aktiv-Gradient
- iOS-Tap-Issues mit onclick-Attribut → Event-Delegation als zweite Schicht
- Cache-Version `miesmuschel-v17` (vor jedem UI-Update bumpen!)

---

## 5. Web Push-Bridge via GitHub Actions

**Problem:** Apple blockt Web-Push aus Anthropic-Cloud-Sandbox (HTTP 403 Allowlist-Host-Restriction).

**Lösung:**
- Cloud-Routine pushed Daten zu GitHub
- `.github/workflows/web-push.yml` triggert auf:
  - `data/tipps/*.json`
  - `data/ergebnisse/*.json`
  - `data/tipps_wochenende/*.json`
  - `data/tipps_woche/*.json`
- Mode-Detection (4 Modi) → Schema-Fix + JS-Wrapper + Push
- `send_push.py --mode <tipps|auswertung|wochenende|woche>`

### Aktuelle Push-Subscription (Stand 01.05.2026)
```
endpoint: https://web.push.apple.com/QOnqknSV5pKUZB-jDaFQ7lo0RitRbpq3_aBv4O3EtVJERKQGbZ1OK0Nq8T_u2kUkxAFk4IcyzobrbdPGAxiRYYc1KD3jDyKCm_UKgrDGSOBP2DAvBOPCV6pw8SXdcod9dGoyXWZc6jY1GKu0YekXOZAuRg6RrB1fuxM3g5RBBLs
p256dh:   BAMNY9Tt0aAth9zvTelWJzgGFptsk7QcKnWGHhoLN6Tw4nRNVsWt8QiP3h2bvmOiPQwUl9ptX2ZLXkZe7mFiLLY
auth:     y-aJ0ii80-DjklEwr5MvKg
```

GitHub Secret `PUSH_SUB` aktualisiert (Status 204) + lokales Backup `.claude/push_subscription.json`.

### Wenn Subscription kaputt
1. Melvi tippt im PWA-Footer "🔔 Push aktivieren" → kopiert JSON
2. Du updatest GitHub Secret `PUSH_SUB` via API (siehe Memory `reference_routines.md`)
3. Backup `.claude/push_subscription.json` aktualisieren

---

## 6. Hard-Cap + Diversifikations-System (3 Schichten)

1. **Routine-Prompts:** alle Tipps-Routinen sagen `!!! HARTLIMIT: MAX 5 TIPPS PRO SPIEL !!!`
2. **Schema-Mapper (`fix_schema.py`):**
   - Cappt automatisch auf 5 Tipps/Spiel mit `(kategorie_priority, -edge_prozent)`-Sort
   - **Layer-1 hartcoded:** max 1 Bein pro Spiel pro Kombi
   - Bereinigt einzeltipps[] und droppt Kombis mit kaputten Refs
   - **Bug-Fix 01.05.:** `tipp_id` → `id` Normalisierung (vorher droppte Mapper alle einzeltipps + kombis stillschweigend)
3. **Layer-2 Lesson-basiert:** Spiel-Sieg-Outcome (ML/DC/Spread/HZ) max in Safe-Kombi. Andere Kombis nutzen Total/Player/Tor. Schema-Mapper warnt bei Verstoß, fixt aber nicht hart (semantisch komplex).

### Best-of-Philosophie
**Tagestipps:** 8-12 Einzeltipps · **Wochenende:** 8-12 (über 2 Tage Pool) · **Woche:** 8-12 (über 7 Tage Pool). NICHT auffüllen wenn Qualität nicht da. Lieber 6 starke als 14 mittelmäßige.

---

## 7. Profit-Hebel (Stand 02.05.)

Drei Hartregeln im System die zusammen +5-10% ROI bringen sollten:

### A) Quoten-Verifikation (PFLICHT)
Kein SAFE/VALUE ohne via Aggregator (oddschecker, sportsgambler, betexplorer, oddsshark, oddstrader) verifizierte bet365-Quote. Sonst max WACKEL mit `~`-Präfix.

### B) Pinnacle-Fair-Line
Pinnacle = schärfster Buchmacher. Edge nur wenn bet365 spürbar besser:
- `>=3%` über Pinnacle: SAFE/VALUE OK
- `0-3%`: max VALUE
- `<0%`: max WACKEL

### C) Beobachtungs-Liga-Modus
Liga mit rolling 30d ROI < -30% bei min. 4 Tipps → in `data/beobachtungs_ligen.json`. Auto-generiert von `statistik_berechnen.py`. Spiele werden gezeigt mit 🔍, aber **NICHT in einzeltipps[]** und **NICHT in Safe/Balance/Risiko-Kombi**. Im Moonshot OK ab Quote ≥5x. Pokale nie betroffen.

**Aktuelle Beobachtungs-Ligen (Stand 02.05.):** 2. Bundesliga (-40%), Serie A (-32%).

### D) Reality-Check pro Tipp
Routine liest `statistik.json` vor jeder Tipp-Generation, fügt in `begruendung` Bilanz-Hinweis ein (z.B. *"Lt. Bilanz: 'Doppelte Chance' bisher 6/6 — Goldgrube"*).

### CLV-Tracking
Auswertungs-Routine erfasst Closing-Quote via WebFetch oddsportal. `clv_prozent` in tipps_ergebnis. Initial viele null, füllt sich auf.

---

## 8. Der Mensch — Melvi

- Deutsch, locker, "bro"-Style
- Claude Max-Abo
- Kein Entwickler — vermeidet Komplexität
- Nutzt Tool primär auf iPhone (PWA)
- E-Mail: msejdiu@b-dhilden.de · GitHub: Melvinhooo
- Will ernsthaft Profit aus dem Hobby machen, nicht nur tracken
- **Constraint: KEINE zusätzlichen Kosten über Max Plan hinaus** (kein Cloud-VM, kein Premium-API)
- **Stil: inkrementell verbessern, nicht umkrempeln** — bestehender Tipp-Stil + Format passen, nur Schwachstellen schärfen

---

## 9. Workflow (täglich autonom)

```
Mo-Fr:
  10:30  Auswertung gestern (statistik + lessons + beobachtungs_ligen update)
         → Push aufs iPhone
  16:00  Tipps Mo-Fr Routine generiert Dossier
         → Push aufs iPhone
  17:15  Tipps-Watchdog (greift wenn 16:00 ausfiel)

Sa+So:
  09:30  Auswertung gestern
         → Push
  10:30  Auswertung-Watchdog
  10:50  Tipps Sa-So Routine (liest frische Bilanz)
         → Push
  11:50  Tipps-Watchdog

Donnerstag zusätzlich:
  18:00  Wochenend-Vorschau (Sa+So Best-of)
         → Push
  19:15  Wochenend-Watchdog

Sonntag zusätzlich:
  18:00  Wochen-Vorschau (Mo-So nächste Woche)
         → Push
  19:15  Wochen-Watchdog
```

→ **~16 Pushs/Woche, alle automatisch.**

---

## 10. Stolperfallen (kumulativ)

1. **PowerShell 5.1 .ps1 ohne BOM** → ASCII-only in .ps1-Files
2. **UTF-8-Double-Encoding** beim HTML-Build → `[System.IO.File]::ReadAllText`
3. **Windows-Explorer versteckt Dateiendungen** → config.json.json-Falle
4. **balldontlie Free-Tier** kann keine Spieler-Stats → Routinen ergänzen via WebSearch
5. **DFB-Pokal/Coppa/FA Cup** nicht im football-data Free-Tier → Routinen via WebSearch
6. **fetch() auf file:// geht nicht** → daher `*.js` als Script statt JSON
7. **Service-Worker-Cache** → bei UI-Änderungen `CACHE` Version in `sw.js` hochdrehen (aktuell **v17**). Sonst sieht User alte Version.
8. **Keine Browser-Storage-APIs** (CLAUDE.md verbietet localStorage)
9. **iOS-PWA-Push** funktioniert NUR via "Zum Home-Bildschirm". Aus Safari-Tab raus blockt iOS Permission.
10. **Cron in UTC** → Ende Oktober 2026 alle Cron-Strings +1h für DST.
11. **Apple Push-Subscription kann sterben ohne 410-Fehler** (PWA-Reinstall, Geräte-Wechsel) → wenn keine Pushs ankommen aber 201-Status: neue Sub holen + Secret + Backup updaten.
12. **PWA-Cache hartnäckig auf iOS** → wenn neue UI nicht erscheint: PWA löschen + Safari aufrufen + neu zum Home-Bildschirm.
13. **`tipp_id` vs `id` Bug** war in Schema-Mapper, jetzt mit Normalisierung gefixt.
14. **Stream-Timeout bei vielen Spielen** (>20) → Cloud-Routine kann Mini-Files nicht fertig schreiben → einzeltipps + kombis bleiben leer. Manuelle Reparatur nötig (siehe `data/tipps/2026-05-02.json` Reparatur am 02.05. Abend).
15. **Sub-Agents bleiben oft im Plan-Mode hängen** wenn Plan-Mode aktiv ist — User-Prompt "kein Plan-Modus" reicht nicht. Lösung: Plan-Mode komplett beenden via ExitPlanMode bevor Sub-Agents gestartet werden, ODER Sub-Agent als sequentielle Iteration im Hauptchat machen.

---

## 11. Wett-Regel-Kurzfassung (Details in CLAUDE.md)

**Verboten** (nie empfehlen):
- Fußball: Eckbälle, Karten
- NBA: Einzel-Rebounds, Assists, Steals, Blocks, Turnovers, PRA-Kombos, Pkt+Reb/Ast-Kombos, Einzel-3er

**bet365-Sonderregeln:**
- **2:0-Insurance** (BL+CL nur, nur Sieg-Tipps): Sieg-Tipp gilt als gewonnen sobald Tipp-Team 2:0 führte
- **Einwechslungs-Boost** (Torschützen): Tor des direkten Ersatzspielers zählt für Tipp-Spieler — aber NUR wenn Tipp-Spieler X selbst ausgewechselt wurde

**NBA-Player-Punkte/DD:** seit Lesson 26.04. **Markt-Boykott**: nicht in Einzeltipps, nur als optionales Bein in Risiko/Moonshot-Kombi.

**Einsatz-Limits:** Einzel SAFE/VALUE 1-2%, Einzel WACKEL 0,5-1%, Safe-Kombi 1-2%, Balance 0,5-1%, Risiko max 0,25%, Moonshot max 0,1%.

---

## 12. Ton & Ehrlichkeit

- Deutsch, locker, Kumpel-Analyst
- "Sieht nach Wert aus" statt "Jackpot winkt"
- Coinflip-Spiele markieren und zum Überspringen empfehlen
- Bei Fehlern: sofort zugeben, nicht rausreden
- User-Ideen nicht als eigene verkaufen
- Kombi-Quoten IMMER nachrechnen
- **Inkrementelle Verbesserungen, nicht Stil umkrempeln**

---

## 13. Was gerade läuft (Stand 02.05.2026 Abend)

- ✅ Cloud-Autopilot (12 Routinen)
- ✅ iOS-Web-Push direkt aus PWA via GitHub Action Bridge
- ✅ Quoten-Hartregel + Pinnacle-Edge-Filter + Beobachtungs-Liga-Filter
- ✅ Auto-generierte Beobachtungs-Liga-Liste
- ✅ CLV-Tracking-Pipeline
- ✅ Dynamischer PWA-Header
- ✅ Service Worker v17
- ✅ Mode-Pill-Bar (3 Modi: Täglich / Wochenende / Woche)
- ✅ Best-of-Philosophie + Layer-1+2 Diversifikation
- ✅ Reminder am 18.05. für Vorschau-Performance-Review
- ✅ Reparatur-Mechanik für Stream-Timeout-Failures (manuell, sub-agent oder direkt)

### Stats
**~85+ Tipps · 62% Trefferquote · ROI ~+3-4%.**

### Known Issues / TODOs für nächsten Chat
1. **Stream-Timeout bei großen Spielmengen** — passiert bei Sa-So-Tipps wenn 25+ Spiele. Routine schreibt `spiele[].tipps[]` aber NICHT `einzeltipps[]` + `kombis[]`. **TODO:** Routine-Prompt anpassen damit sie zuerst die Mini-Files für einzeltipps + kombis schreibt (kleinere Token-Last) und Spiele danach. Oder Spiel-Anzahl auf max 15-20 begrenzen mit ehrlicher Auswahl der wichtigsten Ligen.
2. **Tipps-Watchdogs senden Direct-Push** (alte Subscription im Prompt) — bei Hauptroutine-Fehler würden Watchdogs Alert-Push direkt aus Cloud schicken, was Apple blockt. Bisher nicht aufgefallen weil Watchdogs eh volle Generation machen + dann via Action Push schicken. Aber theoretisch: Subscription in Tipps-Watchdog-Prompts auf neue updaten.
3. **PWA-Cache-Probleme** — iOS-User müssen oft PWA neu installieren bei UI-Updates. Vielleicht aggressivere SW-Update-Logik einbauen.
4. **Vorschau-Auswertung** ist Option A (Snapshot) — Reminder am 18.05. fragt ob Option B (separate Statistik-Streams) gebaut werden soll.

### Letzte Reparaturen
- **02.05.** `data/tipps/2026-05-02.json` einzeltipps + kombis manuell nachgereicht (10 Einzeltipps + 4 Kombis aus 76 spiele[].tipps[] rekonstruiert). Routine war bei 28 Spielen ausgestiegen.
- **01.05.** `data/tipps/2026-05-01.json` analog repariert. Plus `tipp_id` → `id` Bug-Fix im Mapper.
- **01.05.** Wochenende-Vorschau 02.05. + Wochen-Vorschau 04.05. manuell mit Best-of-Philosophie generiert (Probelauf vor Cloud-Routine-Cron).

### Nächste Auto-Runs
- **Sa 02.05. 09:30** Auswertung Fr (LIVE)
- **Sa 02.05. 10:50** Tipps Sa (LIVE) — manuell repariert weil Cloud-Routine ausgestiegen war
- **So 03.05. 09:30** Auswertung Sa
- **So 03.05. 10:50** Tipps So
- **So 03.05. 18:00** Wochen-Vorschau Mo-So nächste Woche (überschreibt manuelle Probe)
- **Do 07.05. 18:00** Wochenend-Vorschau Sa 09.05. + So 10.05.

---

## 14. Erste Nachricht an Melvi nach Handoff

> "Ok, bin auf Stand. HANDOFF, CLAUDE.md, Memory, lessons.json, beobachtungs_ligen.json, letzte ergebnisse gelesen.
> Aktuelle Bilanz: [X] Tipps · Trefferquote Y% · ROI Z%.
> Beobachtungs-Ligen: [Liste].
> 12 Cloud-Routinen aktiv, 3 Modi in der App, alle Pushs funktionieren.
> Nächste Auto-Runs: [Zeit].
> Was steht an?"

---

**Sei ehrlich, rechne Kombis nach, respektiere die Regeln, ändere nicht den Stil — schärfe nur. Das Tool lebt von Konsistenz, nicht von Hype.** 🐚
