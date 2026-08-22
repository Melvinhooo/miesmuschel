# Urlaubs-Check — Stand 22.08.2026

Was läuft ohne dich, wo liegen die Grenzen. Kurzfassung für die Rückkehr.

## Zeitplan (alle Zeiten Berlin, MESZ)

| Wann | Was | Schicht |
|---|---|---|
| täglich 08:00 | Auswertung von gestern | Cloud, Haupt |
| täglich 09:00 | Auswertungs-Watchdog | Cloud, Backup |
| täglich 12:45 | Auswertungs-Backstop | GitHub Action, letzte Schicht |
| Mo–Fr 13:30 | Tages-Tipps | GitHub Action, Haupt |
| Mo–Fr 14:30 | Tipps-Watchdog | Cloud, Backup |
| Mo–Fr 15:15 | Tipps-Backstop | GitHub Action, letzte Schicht |
| Sa+So 10:00 | Tages-Tipps | Cloud, Haupt |
| Sa+So 11:00 | Tipps-Watchdog | Cloud, Backup |
| Sa+So 12:00 | Tipps-Backstop | GitHub Action, letzte Schicht |
| Do 18:00 / 19:15 / 20:30 | Wochenend-Vorschau, Watchdog, Backstop | Cloud / Cloud / Action |
| So 18:00 / 19:15 / 20:30 | Wochen-Vorschau, Watchdog, Backstop | Cloud / Cloud / Action |
| So 21:00 | Maintenance + Kader-Auffrischung | GitHub Action |
| bei jedem Push | Schema-Fix, JS-Wrapper, iPhone-Push | GitHub Action |

Jede Kette prüft **Inhalt, nicht nur Existenz** — ein leeres Dossier löst die nächste Schicht aus.

## Was das Tool von allein tut

- **Auswertet und lernt**: jeden Morgen Ergebnisse holen, volle Spiel-Analyse, bis zu 4 Lessons, Statistik neu rechnen. Daraus entstehen Goldgruben-, Bluter- und Beobachtungs-Listen, die die Tipps-Routinen am selben Tag lesen.
- **Kader aktuell halten**: Maintenance frischt `kader_wechsel_2026.json` sonntags per WebSearch auf; die Auswertung ergänzt sie, wenn ein falsch zugeordneter Spieler auffällt. Der Schema-Mapper droppt Tipps auf Spieler, die den Verein verlassen haben.
- **Zeitfenster erzwingen**: Tages-Dossier = nur dieser Tag, Wochenende = Sa+So, Woche = Mo–So. Spiele außerhalb fliegen mechanisch raus.
- **Sich selbst nicht überschreiben**: abgeschlossene Dossiers werden von keinem Hart-Validator mehr verändert.

## Was du bei Rückkehr prüfen solltest

1. **PWA öffnen.** Steht oben eine rote Box „Veraltetes Dossier"? Dann ist die Tipps-Kette an dem Tag komplett ausgefallen — Datum in der Box sagt seit wann.
2. **Tab Historie**: ROI und Trefferquote plausibel? Statistik wächst nur, wenn die Auswertung lief.
3. **Kasse**: `data/kasse.json` steht auf 1000€ und `stufe_2_freigeschaltet: false`. Wenn du zwischendurch ein- oder ausgezahlt hast, hier korrigieren — die Routinen rechnen alle Einsätze daraus.
4. **GitHub Actions-Tab**: rote Läufe? Die Backstops sind auf `continue-on-error`, melden also nie „failure" — rote Läufe wären echte Probleme.

## Bekannte Grenzen

- **Push-Benachrichtigungen** können still sterben (PWA-Neuinstallation, Gerätewechsel). Wenn keine Pushs mehr ankommen: im PWA-Footer „🔔 Push aktivieren" tippen und den Code an Claude geben.
- **Zeitumstellung 25.10.2026**: Berlin wechselt auf MEZ, alle Cron-Zeiten sind UTC. Dadurch laufen alle Routinen eine Stunde früher in lokaler Zeit — die Reihenfolge bleibt gleich und alle Slots bleiben sinnvoll (Auswertung 07:00, Sa/So-Tipps 09:00, Mo–Fr-Tipps 12:30). **Kein Eingriff nötig**, nur zur Info.
- **Transferfenster schließt 31.08.2026.** Bis dahin ändern sich Kader wöchentlich; die Routinen prüfen pro Spiel live, aber `kader_wechsel_2026.json` hinkt zwangsläufig etwas hinterher.
- **Recherche-Vorstufe ist abgeschaltet** (failte am Startup). Die Tipps-Routinen recherchieren selbst — das funktioniert, kostet aber mehr Laufzeit pro Lauf.
- **Bundesliga startet 28.08.2026.** Ab dann deutlich mehr Spiele pro Tag; falls Dossiers dann dünn wirken, war es vermutlich ein Stream-Timeout — der Watchdog fängt das ab.

## Spielerschutz

18+ · bet365 DE · Hobby-Wetten · Sucht-Hilfe BZgA: **0800 1372700**
Keine Einnahmequelle. Nur setzen, was du verlieren kannst. Stress → Pause. Probleme → Hilfe holen.
Das Tool läuft im Urlaub weiter — es erwartet aber nicht, dass du täglich setzt.
