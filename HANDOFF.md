# 🐚 HANDOFF — Magische Miesmuschel

> **Wenn du neu in diesen Chat kommst: lies dieses Dokument ZUERST.**
> Stand: 27.04.2026 abends — komplett ueberarbeitet nach Migration zu Cloud-Routines + Web-Push + neuen Profit-Hebeln.

---

## 0. Pflicht-Reihenfolge zum Einlesen

1. **`CLAUDE.md`** — alle Regeln, verbotenen Wettarten, Tonalitaet
2. **`README.md`** — Bedienungsanleitung fuer den User
3. **`data/lessons.json`** — alle Wett-Lessons (16 Eintraege, Stand 27.04.)
4. **`data/beobachtungs_ligen.json`** — aktuelle Liga-Bluter (auto-generiert)
5. **letzte 3 `data/ergebnisse/*.json`** — aktuelle Form
6. **`data/statistik.json`** — Bilanz inkl. CLV-Aggregation
7. **Dieses Dokument** — Architektur + Stolperfallen

Dann fragst du Melvi: "Wo sollen wir weitermachen?"

---

## 1. Projekt in einem Satz

Privates Hobby-Tool fuer **bet365 DE** von **Melvi**: strukturierte Wett-Vorbereitung
fuer Fussball (BL, 2.BL, PL, LaLiga, Serie A, Ligue 1, CL, EL, Conference, nationale Pokale)
und NBA. **Hobby, keine Einkommensquelle laut UI** — intern wird aber auf echten Profit hingearbeitet.

---

## 2. Technischer Stack (Stand 27.04.2026)

### Hauptdateien
```
Magische Miesmuschel/
├── index.html                   (App-Schale, jetzt mit dynamischem Header + Push-Button)
├── assets/
│   ├── styles.css
│   ├── app.js                   (rendert Tipps + Historie + dynamischen Header)
│   └── icon.svg
├── manifest.webmanifest
├── sw.js                        (Service Worker v4 — Cache + Web Push)
├── data/
│   ├── tipps/YYYY-MM-DD.json    (von Tipps-Routinen geschrieben)
│   ├── ergebnisse/YYYY-MM-DD.json (von Auswertungs-Routine geschrieben, mit CLV)
│   ├── tipps.js                 (auto-generiert)
│   ├── lessons.json             (von Routinen + Hand gepflegt)
│   ├── lessons.js               (auto-generiert)
│   ├── statistik.json           (auto-generiert mit CLV-Aggregation)
│   ├── statistik.js             (auto-generiert)
│   ├── beobachtungs_ligen.json  (NEU: auto-generierte Liga-Bluter-Liste)
│   └── config.json              (API-Keys, GITIGNORED)
├── scripts/
│   ├── ergebnisse_holen.py      (holt Fussball + NBA APIs, wertet Tipps aus)
│   ├── statistik_berechnen.py   (NEU: rechnet auch CLV + schreibt beobachtungs_ligen.json)
│   ├── ergebnisse_holen.bat
│   └── statistik_berechnen.bat
├── archiv/                      (alte HTML-Versionen)
├── .claude/                     (GITIGNORED, lokal only)
│   ├── github_token.txt         (Fine-grained PAT)
│   ├── push.ps1                 (Git push Helper, ASCII only)
│   ├── vapid_keys.txt           (NEU: Web-Push VAPID Public + Private Keys)
│   ├── push_subscription.json   (NEU: Melvis aktuelle iPhone Push-Subscription)
│   └── ...
├── CLAUDE.md
├── README.md
├── HANDOFF.md                   (diese Datei)
└── .gitignore
```

### Externe Services / Stack
| Service | Zweck | Zugriff / Status |
|---|---|---|
| **GitHub** | Hosting + Version | `Melvinhooo/miesmuschel` public · Token in `.claude/github_token.txt` |
| **GitHub Pages** | Live-App | https://melvinhooo.github.io/miesmuschel/ |
| **football-data.org** | Fussball-Ergebnisse | Free Tier, Key in `data/config.json` |
| **balldontlie.io** | NBA-Spiele | Free Tier (nur /games + /teams), Key in `data/config.json` |
| **Anthropic Cloud Routines** | Autopilot | `/schedule`-Routines, im Max-Plan inklusive |
| **Apple Push Notification Service** | Web-Push aufs iPhone | VAPID-basiert, kostenlos |
| **Python 3** | Lokale Scripts + Cloud-Sandbox | `requests`, `pywebpush` |

---

## 3. Cloud-Routines (Autopilot)

Drei Routines laufen in Anthropic-Cloud (NICHT auf Melvis Laptop). IDs:

| Routine | Cron (UTC) | Berlin (MESZ) | Trigger-ID |
|---|---|---|---|
| `miesmuschel-auswertung-daily` | `30 8 * * *` | taeglich 10:30 | `trig_01BP9meTHCX6R5mgAJf3QT94` |
| `miesmuschel-tipps-mo-fr` | `0 14 * * 1-5` | Mo-Fr 16:00 | `trig_011ps7wgfJwnLX18nUeZV3nu` |
| `miesmuschel-tipps-sa-so` | `30 9 * * 6,0` | Sa+So 11:30 | `trig_01MPfUoxZbHYUA4K6CdQb6G3` |

Verwalten via `RemoteTrigger`-Tool (list/get/update/run) oder UI: https://claude.ai/code/routines

**⚠️ DST-PFLICHT Ende Oktober 2026:** Cron laueft in UTC. Ende Oktober Zeitumstellung -> alle 3 Cron-Strings um +1h anpassen, sonst laufen Routines 1h zu frueh.
- Auswertung: `30 8 * * *` -> `30 9 * * *`
- Tipps Mo-Fr: `0 14 * * 1-5` -> `0 15 * * 1-5`
- Tipps Sa-So: `30 9 * * 6,0` -> `30 10 * * 6,0`

**Lokale alte Tasks** (`mcp__scheduled-tasks__*`) sind alle `enabled=false` als Fallback erhalten. Wenn Cloud-Routines stabil laufen (1+ Woche), koennen sie geloescht werden.

### Was die Routines tun
- **Auswertung (taeglich):** ergebnisse_holen.py → CLV-Erfassung via WebFetch (oddsportal/betexplorer) → statistik_berechnen.py → beobachtungs_ligen.json wird auto-aktualisiert → Lessons-Analyse → git push → Web-Push an Melvi
- **Tipps (Mo-Fr 16:00 + Sa-So 11:30):** Liga-Checkliste komplett → Beobachtungs-Filter aus `data/beobachtungs_ligen.json` → Quoten-Hartregel + Pinnacle-Vergleich → Tipps schreiben → tipps.js regenerieren → git push → Web-Push an Melvi

---

## 4. Web Push Notifications (seit 27.04.)

Echte iOS-PWA-Notifications direkt aus der Miesmuschel-PWA, kein Drittanbieter.

**Setup:**
- VAPID Public Key ist in `index.html` einkompiliert (im inline-Script am Ende)
- VAPID Private Key in jedem Routine-Prompt embedded (nicht im Repo)
- Subscription liegt in `.claude/push_subscription.json` (lokal) + in jedem Routine-Prompt embedded
- Service Worker `sw.js` v4 hat `push`- und `notificationclick`-Handler

**Wenn Subscription kaputt geht** (Melvi loescht PWA, wechselt iPhone):
1. Melvi tippt im PWA-Footer auf "🔔 Push aktivieren" → neue Subscription wird angezeigt
2. Melvi gibt JSON an Claude im Chat
3. Claude updated alle 3 Routine-Prompts via `RemoteTrigger update`
4. Claude updated `.claude/push_subscription.json` als Backup

---

## 5. Profit-Hebel (Stand 27.04. abend)

Drei Hartregeln im System die zusammen +8 bis +13% ROI bringen sollten:

### A) Quoten-Verifikation (PFLICHT 2 in Tipps-Routinen)
Kein SAFE/VALUE ohne via Aggregator (oddschecker, sportsgambler, betexplorer, oddsshark, oddstrader) verifizierte bet365-Quote. Sonst max WACKEL mit `~`-Praefix.

### B) Pinnacle-Fair-Line (PFLICHT 2b in Tipps-Routinen)
Pinnacle ist der schaerfste Buchmacher. Edge nur wenn bet365-Quote spuerbar besser:
- `>=3%` ueber Pinnacle: SAFE/VALUE OK
- `0-3%`: max VALUE
- `<0%`: max WACKEL
Gilt nur fuer Standard-Maerkte (1X2, DC, Handicap, U/O, BTTS). Player-Props sind ausgenommen.

### C) Beobachtungs-Liga-Modus (PFLICHT 0a in Tipps-Routinen)
Liga mit rolling 30-Tage-ROI < -30% bei min. 4 Tipps -> in `data/beobachtungs_ligen.json`. Auto-generiert von `statistik_berechnen.py`. Spiele werden trotzdem in Spiel-Analyse-Tab gezeigt mit 🔍-Markierung, aber **NICHT in einzeltipps[]** und **NICHT in Safe/Balance/Risiko-Kombi**. Im Moonshot OK ab Quote ≥5x. Pokale sind nie betroffen.

Ausstiegs-Kriterium: rolling 30d-ROI > -10% -> Liga faellt automatisch aus der Liste.

### CLV-Tracking (Closing Line Value)
Auswertungs-Routine versucht via WebFetch fuer jeden Tipp die Closing-Quote zu finden, berechnet `clv_prozent`, schreibt in `tipps_ergebnis`. statistik_berechnen.py aggregiert Durchschnitts-CLV. Positive CLV ueber 100+ Tipps = wir sind scharf, langfristig +ROI wahrscheinlich. Anfangs viele `null`-Werte, das ist OK.

---

## 6. Der Mensch — Melvi

- Deutsch, locker, "bro"-Style
- Claude Max-Abo
- Kein Entwickler — vermeidet Komplexitaet
- Nutzt Tool primaer auf iPhone (PWA)
- E-Mail: msejdiu@b-dhilden.de · GitHub: Melvinhooo
- Will ernsthaft Profit aus dem Hobby machen, nicht nur tracken
- Constraint: KEINE zusaetzlichen Kosten ueber Max Plan hinaus (kein Cloud-VM, kein Premium-API)

---

## 7. Design (NICHT anfassen)
- Gradient Tiefsee `#001f3f → #003d6b → #0074b3`
- Fraunces (Headlines) + JetBrains Mono (Body)
- Muschel 🐚 Float-Animation
- Bubbles im Hintergrund
- Mobile-CSS kompakt seit April 2026

---

## 8. Workflow (taeglich)

```
10:30  Auswertungs-Routine: Ergebnisse + CLV + Lessons + statistik + beobachtungs_ligen
       -> Push aufs iPhone
16:00 (Mo-Fr) / 11:30 (Sa-So): Tipps-Routine generiert Dossier
       -> Push aufs iPhone
Abends Melvi tippt bei bet365
Naechster Morgen 10:30: Kreis schliesst sich
```

---

## 9. Stolperfallen

1. **PowerShell 5.1 .ps1 ohne BOM** → ASCII-only in .ps1-Files
2. **UTF-8-Double-Encoding** beim HTML-Build → `[System.IO.File]::ReadAllText`
3. **Windows-Explorer versteckt Dateiendungen** → config.json.json-Falle
4. **balldontlie Free-Tier** kann keine Spieler-Stats → Routinen ergaenzen via WebSearch
5. **DFB-Pokal/Coppa/FA Cup** nicht im football-data Free-Tier → Routinen via WebSearch
6. **fetch() auf file:// geht nicht** → daher `statistik.js` als Script statt JSON
7. **Service-Worker-Cache** → bei Layout-Aenderungen `CACHE` Version in `sw.js` hochdrehen (aktuell v4). Sonst sieht User alte Version.
8. **Keine Browser-Storage-APIs** (CLAUDE.md verbietet localStorage)
9. **iOS-PWA-Push** funktioniert NUR wenn PWA via "Zum Home-Bildschirm" installiert. Aus Safari-Tab raus blockiert iOS die Permission-API.
10. **Cron in UTC** → Ende Oktober 2026 alle Cron-Strings +1h fuer DST anpassen.

---

## 10. Wett-Regel-Kurzfassung (Details in CLAUDE.md)

**Verboten** (nie empfehlen):
- Fussball: Eckbaelle, Karten
- NBA: Einzel-Rebounds, Assists, Steals, Blocks, Turnovers, PRA-Kombos, Pkt+Reb/Ast-Kombos, Einzel-3er

**bet365-Sonderregeln:**
- **2:0-Insurance** (BL+CL nur, nur Sieg-Tipps): Sieg-Tipp gilt als gewonnen sobald Tipp-Team 2:0 fuehrte
- **Einwechslungs-Boost** (Torschuetzen): Tor des direkten Ersatzspielers zaehlt fuer Tipp-Spieler — aber NUR wenn Tipp-Spieler X selbst ausgewechselt wurde

**NBA-Player-Punkte/DD:** seit Lesson 26.04. Markt-Boykott: nicht in Einzeltipps, nur als optionales Bein in Risiko/Moonshot-Kombi.

**Einsatz-Limits:** Einzel SAFE/VALUE 1-2%, Einzel WACKEL 0,5-1%, Safe-Kombi 1-2%, Balance 0,5-1%, Risiko max 0,25%, Moonshot max 0,1%.

---

## 11. Ton & Ehrlichkeit

- Deutsch, locker, Kumpel-Analyst
- "Sieht nach Wert aus" statt "Jackpot winkt"
- Coinflip-Spiele markieren und zum Ueberspringen empfehlen
- Bei Fehlern: sofort zugeben, nicht rausreden
- User-Ideen nicht als eigene verkaufen
- Kombi-Quoten IMMER nachrechnen

---

## 12. Was gerade laeuft (Stand 27.04. abend)

- ✅ Cloud-Autopilot via /schedule (3 Routines)
- ✅ iOS-Web-Push direkt aus PWA
- ✅ Quoten-Hartregel + Pinnacle-Edge-Filter + Beobachtungs-Liga-Filter
- ✅ Auto-generierte Beobachtungs-Liga-Liste
- ✅ CLV-Tracking-Pipeline (initial leer, fuellt sich auf)
- ✅ Dynamischer PWA-Header aus aktuellem tipps.json
- ✅ 16 Lessons in lessons.json
- ✅ Service Worker v4

### Performance-Stand 27.04.
**65 Tipps · 60% Trefferquote · ROI -2,5% · Netto -1,61 U**

Erwartete Wirkung der heute eingebauten Hebel: ROI sollte sich Richtung +3 bis +8% bewegen ueber die naechsten 1-2 Wochen. Erste Validierung morgen 16:00 (erster Tipps-Run unter neuen Regeln). Echte Bewertung in 7-14 Tagen.

### Naechste moegliche Ausbaustufen
- **Stake-Sizing per Half-Kelly** (sobald CLV-Daten zeigen dass Edge real ist)
- **Markt-Spezialisierung** (welche Markt-Typen sind bei uns +ROI? Datenanalyse nach 50+ neuen Tipps)
- **bet365-Limit-Awareness** (wenn das Konto nach Wochen +ROI begrenzt wird, Routinen passen Stake-Empfehlungen an)
- **Cloud-Hosting unabhaengig** (5€/Monat — nicht dringend, Routines laufen sowieso in Cloud)

---

## 13. Erste Nachricht an Melvi nach Handoff

> "Ok, bin auf Stand. CLAUDE.md, lessons.json, beobachtungs_ligen.json, letzte Ergebnisse gelesen.
> Aktuelle Bilanz: [X] Tipps, Trefferquote Y%, ROI Z%.
> Beobachtungs-Ligen aktuell: [Liste].
> Naechster Auto-Run: [Zeit].
> Was soll ich machen?"

---

**Sei ehrlich, rechne Kombis nach, respektiere die Regeln. Das Tool lebt von Konsistenz — nicht von Hype.** 🐚
