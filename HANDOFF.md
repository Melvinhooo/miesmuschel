# 🐚 HANDOFF — Magische Miesmuschel

> **Wenn du neu in diesen Chat kommst: lies dieses Dokument ZUERST.**
> Es fasst alles zusammen was ein Vor-Claude in diesem Projekt aufgebaut hat und
> bringt dich in ~3 Minuten auf denselben Kontext-Stand.

---

## 0. Was du als erstes tust (Pflicht-Reihenfolge)

1. **`CLAUDE.md`** (im Projekt-Root) — alle Regeln, verbotenen Wettarten, Tonalität
2. **`README.md`** — Bedienungsanleitung (was der User macht, welche Scripts)
3. **`data/lessons.json`** — alle Wett-Lessons aus vergangenen Tagen
4. **Letzte 3 Dateien in `data/ergebnisse/`** — aktuelle Form-Trends
5. **`data/statistik.json`** — aktuelle Bilanz-Kennzahlen
6. **Dieses Dokument hier** — Projekt-Meta-Wissen + Stolperfallen

Dann fragst du den User „Wo sollen wir weitermachen?" und bist auf Stand.

---

## 1. Projekt in einem Satz

Privates Hobby-Tool für **bet365 DE** von **Melvi**: strukturierte Wett-Vorbereitung
für Fußball (BL, 2.BL, PL, LaLiga, Serie A, Ligue 1, CL, EL, nationale Pokale)
und NBA (Regular Season, Play-In, Playoffs). **Keine Einnahmequelle.** Spielerschutz
ist Pflicht (BZgA 0800 1372700 im Footer).

---

## 2. Technischer Stack (Stand ~April 2026)

### Hauptdateien
```
Magische Miesmuschel/
├── index.html                   (App-Schale)
├── assets/
│   ├── styles.css               (Design: Tiefsee, Muschel, Blasen — NICHT ändern)
│   ├── app.js                   (Vanilla JS, rendert tipps.js + statistik.js)
│   └── icon.svg                 (PWA-Icon)
├── manifest.webmanifest         (PWA-Manifest)
├── sw.js                        (Service Worker für Offline/Cache)
├── data/
│   ├── tipps/YYYY-MM-DD.json    (ein Dossier pro Tag)
│   ├── ergebnisse/YYYY-MM-DD.json (ein Auswertungs-File pro Tag)
│   ├── tipps.js                 (auto-generiert aus aktuellster tipps/*.json)
│   ├── lessons.json             (Lessons Learned — ergänzt durch Analyse-Task)
│   ├── lessons.js               (auto-generiert aus lessons.json)
│   ├── statistik.json           (aggregierte Bilanz)
│   ├── statistik.js             (auto-generiert, für App)
│   └── config.json              (API-Keys, GITIGNORED, NIE committen)
├── scripts/
│   ├── ergebnisse_holen.py      (holt Fußball-APIs + NBA + wertet Tipps aus)
│   ├── ergebnisse_holen.bat     (Windows-Doppelklick-Starter)
│   ├── statistik_berechnen.py   (aggregiert ergebnisse -> statistik)
│   └── statistik_berechnen.bat
├── archiv/                      (alte HTML-Versionen v13, v22)
├── .claude/                     (GITIGNORED, lokal only)
│   ├── github_token.txt         (Fine-grained PAT, 1 Jahr gültig, repo-only)
│   ├── push.ps1                 (Git commit + push Helper — ASCII only!)
│   ├── build_index.ps1          (baut index.html aus altem v22 — nur noch selten nötig)
│   ├── make-icon.ps1            (generiert muschel.ico)
│   └── muschel.ico              (Windows-Icon für Desktop-Shortcut)
├── CLAUDE.md                    (VERBINDLICHE Regeln)
├── README.md                    (User-Bedienungsanleitung)
├── HANDOFF.md                   (diese Datei)
└── .gitignore                   (schließt .claude/, config.json aus)
```

### Externe Services
| Service | Zweck | Zugriff |
|---|---|---|
| **GitHub** | Hosting (Pages) + Version | Repo: `Melvinhooo/miesmuschel` (public) · Token in `.claude/github_token.txt` |
| **GitHub Pages** | Live-App | URL: `https://melvinhooo.github.io/miesmuschel/` |
| **football-data.org** | Fußball-Ergebnisse | Key in `data/config.json` (`football_data_key`) · Free-Tier 10 req/min · BL, 2.BL, PL, PD, SA, CL, FL1 verfügbar · DFB-Pokal + Coppa Italia NICHT im Free-Tier |
| **balldontlie.io** | NBA-Spiele | Key in `data/config.json` (`balldontlie_key`) · Free-Tier nur /games + /teams · `/stats` (Spielerpunkte) braucht GOAT-Abo ($9/Monat, aktuell NICHT gebucht) |
| **Python 3.14** | Scripts lokal | Installiert unter `py`-Launcher. `requests` wird von .bat auto-installiert |
| **PowerShell 5.1** | Windows-System | Wichtig: liest .ps1 ohne BOM als Windows-1252 → nur ASCII in .ps1 verwenden |

---

## 3. Scheduled Tasks (Autopilot)

Drei Tasks laufen automatisch auf Melvi's Laptop (wenn er eingeschaltet ist):

| Task-ID | Cron | Was |
|---|---|---|
| `miesmuschel-daily-tipps` | `30 10 * * *` (täglich 10:30) | Holt gestrige Ergebnisse via API + WebSearch, analysiert Muster, ergänzt `data/lessons.json` wenn >10 Tipps klares Muster zeigen, pusht |
| `miesmuschel-tipps-mo-fr` | `0 16 * * 1-5` (Mo-Fr 16:00) | Generiert neues Dossier für **heute 16:00 bis morgen 06:00** (inkl. NBA-Nacht), pusht |
| `miesmuschel-tipps-sa-so` | `30 11 * * 6,0` (Sa+So 11:30) | Generiert neues Dossier für **heute 11:30 bis morgen 06:00**, pusht |

Gespeichert unter `C:\Users\melvi\.claude\scheduled-tasks\<task-id>\SKILL.md`.
Mit `mcp__scheduled-tasks__list_scheduled_tasks` sieht man den Zustand, mit
`mcp__scheduled-tasks__update_scheduled_task` kann man Prompts/Zeiten anpassen.

**Wichtig:** Tasks laufen lokal. Wenn Laptop aus → kein Autopilot.

---

## 4. Der Mensch — Melvi

- Deutsch. Kommuniziert locker, „bro"-Style, Kumpel-Ton.
- Claude Max-Abo (inkl. Scheduled Tasks + iPhone-App).
- Kein Entwickler — vermeidet Komplexität. Klare Schritt-für-Schritt-Anleitungen ohne Fachjargon.
- Nutzt das Tool primär **auf dem iPhone** (PWA auf Home-Screen installiert).
- Laptop = Autopilot-Server, meistens zugeklappt am Netz.
- Hasst Verkacken. Will lieber klar „los" sagen und dich machen lassen.
- E-Mail: `msejdiu@b-dhilden.de` · GitHub: `Melvinhooo`

---

## 5. Design-Regeln (NICHT anfassen!)

- **Gradient** Tiefsee `#001f3f → #003d6b → #0074b3`
- **Schriften** Fraunces (Headlines) + JetBrains Mono (Body)
- **Muschel** 🐚 mit Float-Animation
- **Bubbles** steigen im Hintergrund
- **Kategorie-Farben:** safe=grün, value=gold, wackel=orange, risk=rot/lila, moonshot=lila/gold
- Mobile-CSS (iPhone) ist seit April 2026 stark kompaktiert — siehe `@media (max-width: 700px)`

Wenn Design-Änderungen nötig: nur Größen/Abstände, nie Farben/Schriften/Layout-Philosophie.

---

## 6. Workflow — wie das System läuft

### A) Ein Tag im Leben
```
10:30  Analyse-Task: Ergebnisse gestern, Lessons-Check, GitHub-Push
16:00 (Mo-Fr) oder 11:30 (Sa-So): Tipps-Task schreibt Dossier für heute→morgen 06:00
       Push zu GitHub
       iPhone-App zeigt neue Tipps
Abends Melvi tippt bei bet365
Spiele laufen
Nächster Morgen 10:30: Kreis schließt sich
```

### B) Wenn Melvi im Chat was will

**„Neue Tipps für heute"** →
1. CLAUDE.md + lessons.json + letzte Ergebnisse lesen
2. WebSearch: Spiele heute in CLAUDE.md-Ligen
3. `data/tipps/YYYY-MM-DD.json` schreiben (5-10 Spiele, 10-14 Einzeltipps, 4 Kombis)
4. `data/tipps.js` regenerieren (PowerShell-Wrapper)
5. `.claude/push.ps1 "Commit-Message"` aufrufen

**„Push neue Ergebnisse"** → `.claude/push.ps1 "Nachricht"`

**„Ergebnisse holen"** → `py -3 scripts/ergebnisse_holen.py YYYY-MM-DD` (optional Datum; ohne = alle offenen Tage)

### C) tipps.js regenerieren (PowerShell-Snippet)
```powershell
$src = 'C:\Users\melvi\Downloads\Magische Miesmuschel\data\tipps\YYYY-MM-DD.json'
$dst = 'C:\Users\melvi\Downloads\Magische Miesmuschel\data\tipps.js'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$json = [System.IO.File]::ReadAllText($src, $utf8NoBom)
[System.IO.File]::WriteAllText($dst, ("// Auto-generiert`nwindow.__MIESMUSCHEL_TIPPS = " + $json + ";`n"), $utf8NoBom)
```

---

## 7. Stolperfallen — erlittene, nicht wiederholen

1. **PowerShell 5.1 + .ps1 ohne BOM** → Non-ASCII-Zeichen (Em-Dash —, Umlaute in Kommentaren) zerschießen das Parsing. **Regel: .ps1-Scripts ASCII-only schreiben.**

2. **UTF-8-Double-Encoding** beim HTML-Build: Wenn man v22.html mit `Get-Content -Encoding UTF8` liest und Output ohne BOM schreibt, kann passieren dass Emojis doppelt encoded werden. Lösung: `[System.IO.File]::ReadAllText($path, [System.Text.UTF8Encoding]::new($false))`.

3. **Windows-Explorer versteckt Dateiendungen** → User hat `config.json` zu `config.json.json` umbenannt. Script hat Fallback, User-README warnt jetzt.

4. **balldontlie Free-Tier** kann keine Spieler-Stats. Daher: alle NBA-Player-Props (Punkte, DD, TD) bleiben nach `ergebnisse_holen.py` „offen" → Analyse-Task (10:30) muss per WebSearch (ESPN, Kicker, Sofascore) manuell ergänzen.

5. **DFB-Pokal + Coppa Italia** nicht im football-data-Free-Tier → bleiben auch offen, müssen manuell oder via WebSearch eingetragen werden.

6. **fetch() auf file:// geht nicht** → daher das `statistik.json` auch als `statistik.js` geschrieben wird (setzt `window.__MIESMUSCHEL_STAT`). Nie die .json direkt in index.html laden.

7. **Service-Worker-Cache** → CSS/JS-Änderungen werden nicht sofort am iPhone sichtbar. Bei Layout-Änderungen: `CACHE` Version in `sw.js` hochdrehen (`miesmuschel-v1` → `v2` → `v3`...), sonst bleibt Nutzer bei alter Version.

8. **Keine Browser-Storage-APIs** verwenden (localStorage/sessionStorage) → alle Persistenz läuft über JSON-Dateien. CLAUDE.md sagt das.

---

## 8. Wett-Regel-Kurzfassung (Details in CLAUDE.md)

**Verboten** (nie empfehlen):
- Fußball: Eckbälle, Karten
- NBA: Einzel-Rebounds, Assists, Steals, Blocks, Turnovers, PRA-Kombos, Pkt+Reb/Ast-Kombos, Einzel-3er

**Einsatz-Limits:**
- Einzel SAFE/VALUE: 1–2 % Kasse
- Einzel WACKEL: 0,5–1 %
- Safe-Kombi: 1–2 % · Balance: 0,5–1 % · Risiko: max 0,25 % · Moonshot: max 0,1 %

**Kombi-Grundsätze:**
- NBA-Player-Props **NIE als SAFE** (Playoff-Varianz)
- Safe-Kombi: nur SAFE-Beine
- Risiko-Kombi: 3–5 Beine mit Quote 3.0+, keine Banker-Füller
- Keine Spieler-Stacks über mehrere Kombis (Wemby-Lesson)
- Gesamtquote IMMER nachrechnen — „~8" wenn 5.4 rauskommt ist verboten

---

## 9. Ton & Ehrlichkeit

- Deutsch, locker, Kumpel-Analyst
- Keine englischen Wettbegriffe („Beide Teams treffen", nicht „BTTS")
- „Sieht nach Wert aus" statt „Jackpot winkt"
- Coinflip-Spiele markieren und zum Überspringen empfehlen
- Bei Fehlern: sofort zugeben, nicht rausreden
- User-Ideen nicht als eigene Analyse verkaufen

---

## 10. Was gerade im Fluss ist (Stand bei Handoff-Schreibzeit)

- ✅ Autopilot (3 Scheduled Tasks) läuft
- ✅ iPhone-PWA installiert und kompakt
- ✅ Fine-grained Token in `.claude/github_token.txt`, 1 Jahr gültig
- ✅ Mobile-CSS seit April 2026 kompakt
- ✅ Service Worker v2
- 🔄 Lessons wachsen automatisch durch 10:30-Task
- 🔄 Melvi nutzt Tool vor allem auf iPhone

**Offene Themen / mögliche nächste Ausbaustufen:**
- Langfristig: Cloud-Hosting damit PC nicht immer an sein muss (5 €/Monat, nicht dringend)
- balldontlie GOAT ($9/Monat) für Auto-Spielerpunkte (nice-to-have)
- Mehrere Kassen-Profile / verschiedene Einsatz-Strategien tracken (idee, nicht gebaut)

---

## 11. Erste Nachricht an Melvi nach Handoff

> „Ok, bin auf Stand. CLAUDE.md, lessons.json, letzte Ergebnisse gelesen.
> Aktuell hast du [X] Tipps Historie, Trefferquote Y%, ROI Z%.
> Autopilot läuft (nächster Run: ...).
> Was soll ich machen?"

---

**Viel Glück, neuer Claude. Sei ehrlich, rechne Kombis nach, respektiere die Regeln.
Das Tool lebt von Konsistenz — nicht von Hype.** 🐚
