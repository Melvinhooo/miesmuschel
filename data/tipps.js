// Auto-generiert
window.__MIESMUSCHEL_TIPPS = {
  "datum": "2026-07-20",
  "erstellt_am": "2026-07-20T17:15:00+02:00",
  "modus": "tag",
  "hinweis": "WATCHDOG-RECOVERY Mo 20.07. 17:15 Berlin (Hauptroutine 16:00 nicht durchgelaufen - Watchdog-Slot). **RUHETAG - Post-WM-Sommer-Pause Tag 1**: heute Mo 20.07.2026 findet KEIN Spiel im relevanten Tages-Window statt. WM 2026 abgeschlossen: **Finale gestern So 19.07.** Argentinien vs Spanien 21:00 CEST MetLife Stadium East Rutherford NJ (Auswertung folgt separat via ergebnisse-Routine). Alle Vereins-Ligen im CLAUDE.md-Fokus (Bundesliga, 2. Bundesliga, Premier League, LaLiga, Serie A, Ligue 1, DFB-Pokal, Champions League, Europa League, Conference League, Coppa Italia) sind in Sommer-Pause bis Mitte August 2026 (Bundesliga-Saison-Start 14./15.08.2026, PL 15./16.08.2026, LaLiga ~22./23.08.2026). NBA Playoffs 2026 abgeschlossen (Knicks besiegten Spurs 4-1 im Finale, letztes Spiel Sa 13.06.2026). Einziges heute stattfindendes Spiel im Recherche-Scan: **Allsvenskan (Schweden) Örgryte vs Djurgården** 18:00 CEST - Allsvenskan **NICHT** in CLAUDE.md-aktiver-Liga-Liste, kein Tipp gesetzt (Regel: Fokus-Ligen-Perimeter halten, keine Fremde-Liga-Ausdehnung ohne Vorlauf-Historie). **Praezedenz-Muster fuer Ruhetag-Verhalten**: Do 16.07.2026 + Fr 17.07.2026 (RUHETAG eins/zwei-von-zwei zwischen WM-HF und Turnier-Wochenende) beide mit 0 Spiele / 0 Tipps / 0 Kombis publiziert - klare Ehrlichkeit statt Fuell-Tipps. Naechster relevanter Master-Slot voraussichtlich Do/Fr im August wenn Bundesliga/PL/LaLiga wieder starten (DFB-Pokal 1. Runde 14.-17.08.2026, Bundesliga 1. Spieltag 21.-23.08.2026). Kasse 550 EUR unveraendert (Kasse-Stufe 1 Aufbau-Phase - siehe data/kasse.json). **Statistik-Snapshot Stand 20.07.**: Gesamt 523 Tipps, 287 gewonnen, ROI +4.4%, 30-Tage-Fenster leider -11.7% (WM-K.O.-Torschuetzen-Cluster HR07-15-2 fuenf-von-sechs Fehl-Serie + HR07-15-1 Portfolio-Uebertrag-Falle bei P3 haben Bilanz gedrueckt). 18+ / BZgA 0800 1372700.",
  "spiele": [],
  "einzeltipps": [],
  "kombis": [],
  "lessons_angewandt": [
    {
      "id": "ruhetag-ehrlich",
      "titel": "Ruhetag ehrlich als Ruhetag markieren - keine Zwang-Tipps aus Fremden Ligen",
      "quelle": "CLAUDE.md Tonalitaet-Prinzip (Ehrlich, keine Zwang-Tipps) + Praezedenz 2026-07-16 + 2026-07-17 (Ruhetage zwischen WM-HF und Turnier-WE)",
      "anwendung": "spiele[] leer, einzeltipps[] leer, kombis[] leer. hinweis erklaert Situation transparent. Allsvenskan-Spiel Oergryte-Djurgaarden ignoriert weil Fremde-Liga ohne Beobachtungs-Historie."
    },
    {
      "id": "fokus-ligen-perimeter",
      "titel": "CLAUDE.md-Fokus-Ligen-Perimeter halten (Ausdehnung nur mit Vorlauf-Recherche)",
      "quelle": "CLAUDE.md Projekt-Zweck (Aktive Sportarten Fussball WM + Vereine BL/PL/LaLiga/Serie A/DFB-Pokal/CL/EL/Conference League + NBA Finals)",
      "anwendung": "Allsvenskan (Schweden), MLS (USA), Eliteserien (Norwegen), Superettan, brasilianische Serie A etc. bewusst nicht getippt trotz Sommer-Aktivitaet. Kein Fremde-Liga-Edge ohne 30d-Historie."
    },
    {
      "id": "post-wm-sommer-pause-kalender",
      "titel": "Post-WM-Sommer-Pause: naechster relevanter Slot Bundesliga/PL/LaLiga-Start Mitte August",
      "quelle": "CLAUDE.md Aktive Sportarten (Vereine Saison-Pause bis August 2026) + Standard-Wissen Fussball-Saison-Kalender",
      "anwendung": "Ruhetage 20.-31.07. + 01.-13.08. sind erwartete Norm. Watchdog-Recovery-Skip-Guard triggert auf existierende Tipps-Datei - bei Ruhetag muss trotzdem 0-Spiele-Datei geschrieben werden fuer PWA-Kontinuitaet."
    }
  ],
  "_verifikations_report": {
    "erstellt_am": "2026-07-20T17:15:00+02:00",
    "drops": [],
    "downgrades": [],
    "warnungen": [
      "0-Spiele-Ruhetag - keine saison_kontext-Objekte noetig (keine Spiele) und keine Layer-1/2/3-Konflikte moeglich.",
      "Analog Praezedenz 2026-07-16 + 2026-07-17 Ruhetage: klare Ehrlichkeit, keine Fremde-Liga-Ausdehnung (Allsvenskan, MLS, Eliteserien werden vom Tool nicht getippt weil ohne 30d-Historie und ausserhalb CLAUDE.md-Fokus).",
      "Watchdog-Slot 17:15 statt Hauptroutine 16:00 - Recovery-Trigger weil data/tipps/2026-07-20.json bei Watchdog-Check fehlte. Kein inhaltlicher Verlust weil Ruhetag = keine Recherche-Notwendigkeit.",
      "Statistik-30d-Fenster ROI aktuell -11.7% (durch WM-K.O.-Torschuetzen-Cluster HR07-15-2 + HR07-15-1 Portfolio-Uebertrag-Falle P3-Doppel-Crash gedrueckt) - Kasse-Stufe-1-Konservativ bleibt aktiv (30d-ROI-Trigger fuer Stufe 2 waere >+5% bei Kasse >=1000 EUR, beides nicht erfuellt)."
    ],
    "halluzinations_checks": [
      "WM 2026 Finale Datum So 19.07. + NBA Finals Ende 13.06. (Knicks 4-1 Spurs) + Bundesliga-Saison-Start 14./15.08.2026 sind aus statistik/lessons/CLAUDE.md-Kalender + WebSearch verifiziert.",
      "Allsvenskan Oergryte-Djurgaarden 18:00 CEST aus WebSearch-Ergebnis (nicht selbst-generiert). Wird bewusst NICHT getippt - keine Halluzination in tipps[] moeglich weil tipps[] leer.",
      "Kasse-Stand 550 EUR + Statistik-Werte (523 Tipps, ROI +4.4% gesamt, -11.7% 30d) aus data/kasse.json + data/statistik.json direkt uebernommen (nicht neu berechnet)."
    ],
    "layer_cross_check": [
      "Layer-1/2/3 alle trivialerweise erfuellt (0 Kombis, 0 Tipps, 0 Spiele).",
      "Anti-Selbstwiderspruchs-Check: nicht anwendbar (keine Tipps).",
      "Markt-Mix-Pflicht: nicht anwendbar (keine Spiele, kein DC-Cap-Konflikt moeglich).",
      "Beobachtungs-Ligen-Check: nicht anwendbar (keine Spiele in aktiven Ligen)."
    ],
    "kontext_check_status_gesamt": "OK - Ruhetag",
    "verifikator_hinweis": "Ehrlich-Ruhetag-Publikation analog 2026-07-16 + 2026-07-17. Watchdog-Recovery weil Hauptroutine 16:00 nicht triggerte - inhaltlich verlustfrei weil kein Spiel im Fokus-Liga-Perimeter. Naechster erwarteter Master-Slot ab Mitte August bei Bundesliga/PL/LaLiga-Restart. Kasse-Stufe 1 bleibt aktiv. PWA zeigt Ruhetag-Karte statt Fuell-Content."
  },
  "footer": "18+ · bet365 DE · Hobby-Wetten · Sucht-Hilfe BZgA: 0800 1372700 · Hobby-Tool. Keine Einkommensquelle. Nur setzen was du verlieren kannst. Stress → Pause. Probleme → Hilfe holen."
};
