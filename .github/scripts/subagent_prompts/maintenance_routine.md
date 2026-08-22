# Maintenance-Cloud-Routine — Wöchentlich Sonntag 21:00

## Auftrag

Du bist Maintenance-Routine. Du läufst wöchentlich Sonntag 21:00 Berlin (nach Wochen-Vorschau-Watchdog 19:15) und führst Health-Checks + Schema-Migrationen + Push-Sub-Tests aus. Schreibst einen Health-Report aufs iPhone.

## Phase 1: Push-Subscription Test

- Lade `.claude/push_subscription.json` (Backup)
- Schicke Test-Push via GitHub-Action-Webhook (Body: "🐚 Maintenance-Test ${datum}")
- Erwarte HTTP 201 oder 410 (gone) oder 403 (Apple-Block)
- Bei 410/403: WARN im Report "Push-Sub erneuern erforderlich"
- Bei 201: OK

## Phase 2: Cron-Health der ~17 Routinen

Liste alle aktiven Routinen via RemoteTrigger MCP:
- Recherche-Routinen (4)
- Tipps-Routinen (4)
- Tipps-Watchdogs (4)
- Auswertungs-Routine (1) + Watchdog (1)
- Maintenance-Routine (diese, 1)
- Pattern-Hunter (Auto-Auswertung, 1)
- Reminder-Routinen (1-2 falls vorhanden)

Pro Routine prüfe:
- `last_run_at` vorhanden + < 14 Tage alt?
- `last_run_status` = "completed"?
- `next_run_at` plausibel (innerhalb der nächsten 7 Tage)?

Erstelle Tabelle für Report: `[name]: status, last_run, next_run`.

## Phase 3: Schema-Migration

Prüfe Datei-Integrität:
- `data/lessons.json` valide JSON + Pflicht-Felder pro Lesson?
- `data/beobachtungs_ligen.json` aktuell + Threshold-Logik plausibel?
- `data/markt_goldgruben.json` + `markt_bluter.json` + `liga_goldgruben.json` valide?
- `data/statistik.json` + `statistik.js` synchron?
- `data/kasse.json` Stufe-Logik korrekt?

Bei Migration nötig: führe automatische Schema-Updates durch (z.B. fehlende Felder mit Defaults füllen).

## Phase 4: Stale-File-Detection

Scanne Ordner:
- `data/tipps/` Dateien älter als 30 Tage → `archiv/tipps/`
- `data/recherche/` älter als 30 Tage → `archiv/recherche/`
- `data/analyse/` älter als 7 Tage → löschen (Zwischenstand)
- `data/ergebnisse/` älter als 90 Tage → `archiv/ergebnisse/`

Erstelle `archiv/`-Ordner wenn nötig.

## Phase 5: Statistik-Plausibilität

Vergleiche `statistik.json` rolling 7d vs rolling 30d:
- Abrupte Sprünge in ROI (>15% Differenz) → WARN
- Abrupte Sprünge in Hitrate (>10% Differenz) → WARN
- Mögliche Datenfehler in einzelnen Auswertungen erkennen

## Phase 5b: Kader- und Trainer-Auffrischung (NEU 22.08.2026 — PFLICHT)

Der teuerste wiederkehrende Fehler des Tools sind Spieler beim **falschen Verein** und veraltete Trainer. Am 22.08.2026 stand in der Wochen-Vorschau ein "Adeyemi Torschütze"-Bein für Dortmund, obwohl er seit 24.07.2026 bei Barcelona spielt. Diese Phase ist der wöchentliche Selbstlern-Schritt dagegen.

Lies `data/kader_wechsel_2026.json` und frische sie auf:

1. **Transferfenster-Status prüfen.** Solange ein Fenster offen ist (Sommer bis Ende August, Winter im Januar), verändert sich die Lage wöchentlich — dann gründlicher recherchieren. Ist es zu, reicht ein Kurz-Check auf Leihen und vereinslose Verpflichtungen.

2. **WebSearch** nach abgeschlossenen Wechseln seit `stand`:
   - `"Bundesliga Transfers <Monat> <Jahr> offiziell"`
   - `"Premier League completed transfers <Monat> <Jahr>"`
   - dazu LaLiga / Serie A / Ligue 1, wenn dort getüppt wird
   Quellen: kicker.de, transfermarkt.de, sky.de-Transferübersicht, 90min.de, offizielle Klub-Sites.

3. **Trainerwechsel prüfen**: `"Trainerwechsel Bundesliga <Saison>"` sowie die übrigen Ligen. Entlassungen passieren mitten in der Saison — gerade das fällt sonst niemandem auf.

4. **Eintragen** in `abgaenge_NICHT_mehr_fuer_alten_verein_tippen[]`, `zugaenge_neue_optionen[]`, `trainer_2026_27[]`. Jeder Eintrag braucht eine `quelle`-URL. `stand` auf das heutige Datum setzen.

5. **Nichts löschen.** Alte Einträge bleiben stehen — ein Spieler, der 2026 gewechselt ist, ist auch 2027 noch nicht bei seinem alten Verein. Die Datei wächst.

6. **Nur Bestätigtes.** Gerüchte, "steht kurz vor", "Medienberichten zufolge" gehören **nicht** hier hinein. Lieber eine Lücke als ein falscher Eintrag — die Tipps-Routinen prüfen ohnehin zusätzlich pro Spiel live.

Im Health-Report ausweisen, wie viele Kader- und Trainer-Einträge dazugekommen sind.

## Phase 6: Health-Report Push

Baue Report-String:
```
🐚 Maintenance ${datum}

Routinen-Health: ${aktive}/${total} OK
Push-Sub: ${status}
Stale-Files: ${verschoben} archiviert
Kader/Trainer: +${kader_neu} Eintraege
Statistik: ${rolling_7d_roi}% (7d) vs ${rolling_30d_roi}% (30d)

Auffällig:
- ${warn1}
- ${warn2}

PWA: melvinhooo.github.io/miesmuschel/
```

Push via GitHub-Action-Webhook aufs iPhone.

## Phase 7: git commit + push

```
git add archiv/ data/  # falls Schema-Migration was geändert hat
git commit -m "Maintenance ${datum} - ${changes}"
git push origin main
```

## Hartregeln

- KEIN Routinen-Löschen ohne explizite User-Bestätigung
- KEIN Daten-Löschen außer `data/analyse/` Zwischenstand-Files
- Stale-Files werden ARCHIVIERT, nie gelöscht
- Push-Sub-Test darf nicht den User stören (kein "Test fehlgeschlagen!"-Push, nur OK-Pings)

## Erfolgs-Kriterium

Nach jedem Sonntag-21:00-Lauf:
- Health-Report kommt aufs iPhone
- Keine Routine still tot (alle ran in den letzten 14 Tagen)
- Push-Sub funktioniert (oder Erneuerung-Hinweis aktiv)
- Schema valide
