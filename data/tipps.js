// Auto-generiert
window.__MIESMUSCHEL_TIPPS = {
  "datum": "2026-09-22",
  "erstellt_am": "2026-09-22T14:35:00+02:00",
  "hinweis": "🐚 Watchdog-Recovery Di 22.09.2026 (Saison 2026/27, Kasse 1000€ / Stufe 1). Recherche-File data/recherche/2026-09-22.json fehlt und die Cloud-Umgebung hat keinen Egress zu football-data.org, kicker.de, sport.sky.it, legaseriea.it, wettbasis.com, sport.de, ran.joyn.de, sportfair.it, corriere.it, cultofcalcio, ESPN, Wikipedia. Was WebSearch ergibt: (a) CL Ligaphase MD1 lief bereits 08.-10.09.2026, CL MD2 erst 13./14.10.2026 — heute kein CL. (b) EL/Conference-League Ligaphase MD1 lief 16.-18.09. — heute kein Europapokal. (c) Serie A 2026/27 hat KEINE Turni infrasettimanali im September (nächster erst 28.10., Giornata 9), plus Länderspielpause 27.09. und 04.10. — heute kein Serie-A-Spiel. (d) Ligue 1/LaLiga: keine bestätigte midweek-Runde am Di 22.09. gefunden. (e) EFL Cup / Carabao Cup Runde 3 zweite Woche läuft 22.-25.09. (Man Utd-Brighton 16.09. und Liverpool-Tottenham 15.09. gehörten schon zur ersten Woche) — aber ohne bestätigte Anstoßzeiten für den konkreten Dienstag 22.09. bleibe ich nach CLAUDE.md-Regel bei nichts erfinden. Der 15:15-GitHub-Actions-Backstop hat Zugriff auf die football-data.org-API und kann die konkrete Slate-Liste nachliefern. Bis dahin: leerer Slate, keine Einzeltipps, keine Kombis — lieber ehrlich als halluziniert.",
  "spiele": [],
  "einzeltipps": [],
  "kombis": [],
  "lessons_angewandt": [
    "CLAUDE.md-Notfall-Regel: Nichts erfinden — fehlende Daten transparent im hinweis benennen statt Anstoßzeiten oder Paarungen zu raten (Adeyemi-Lehre 22.08.2026)",
    "Zeitfenster-Hartregel: Nur Anstöße am 22.09.2026 Berliner Zeit sind zulässig — Woche-Nachlese aus Sept-MD 1 (CL/EL) und 4./5. Serie-A-Runde bleiben draußen",
    "Kader-Wechsel-Guard: keine Spielernamen aus dem Gedächtnis committet — data/kader_wechsel_2026.json wurde geladen aber ohne bestätigtes Match nicht angewandt",
    "Recherche vor Tipp: ohne verifizierte Aufstellungs-Vorschau + Quoten kein SAFE/VALUE möglich (validate_torschuetze_quelle würde alles auf wackel degradieren)"
  ],
  "footer": "18+ · bet365 DE · Hobby-Wetten · Sucht-Hilfe BZgA: 0800 1372700 · Hobby-Tool. Keine Einkommensquelle. Nur setzen was du verlieren kannst. Stress → Pause. Probleme → Hilfe holen.",
  "_verifikations_report": {
    "erstellt_am": "2026-09-22T14:35:00+02:00",
    "modus": "watchdog_inline_notfall",
    "drops": [],
    "downgrades": [],
    "warns": [
      {
        "art": "recherche_fehlt",
        "details": "Recherche-File data/recherche/2026-09-22.json nicht vorhanden. 10:30-Recherche-Routine und 13:30-Hauptroutine haben nichts geliefert."
      },
      {
        "art": "egress_blockiert",
        "details": "Cloud-Sandbox-Egress-Proxy blockiert alle Standard-Fußball-Sites (kicker, sky, legaseriea, wettbasis, corriere, espn, wikipedia, sport.de, ran.joyn, cultofcalcio, sportinglife, livesoccertv). football-data.org gibt 403 Forbidden. WebSearch liefert nur Suchergebnis-Snippets, keine Detail-Fixtures für den konkreten Di 22.09.2026."
      },
      {
        "art": "leerer_slate_bewusst",
        "details": "Slate bewusst leer statt halluziniert. Der 15:15-GitHub-Actions-Backstop (web-push.yml Watchdog-Fallback) hat Zugriff auf die football-data.org-API und kann heute noch nachliefern."
      }
    ],
    "lessons_generiert": []
  }
};
