// Auto-generiert
window.__MIESMUSCHEL_TIPPS = {
  "datum": "2026-07-21",
  "erstellt_am": "2026-07-21T17:15:00+02:00",
  "modus": "tag",
  "hinweis": "WATCHDOG-SLOT Di 21.07. 17:15 Berlin (Hauptroutine 16:00 nicht gelaufen - Watchdog uebernimmt). **RUHETAG - Post-WM-Sommer-Pause Tag 2**: heute Di 21.07.2026 findet KEIN Spiel in einer CLAUDE.md-Fokus-Liga im Tages-Window statt. WM 2026 abgeschlossen (Finale So 19.07. Argentinien vs Spanien, MetLife Stadium East Rutherford NJ - Auswertung via ergebnisse-Routine). Alle Vereins-Ligen (Bundesliga, 2. Bundesliga, Premier League, LaLiga, Serie A, Ligue 1, DFB-Pokal, Champions League, Europa League, Conference League, Coppa Italia) in Sommer-Pause bis Mitte August 2026 (DFB-Pokal 1. Runde 14.-17.08., Bundesliga 1. Spieltag 21.-23.08., PL 15./16.08., LaLiga ~22./23.08.). NBA Playoffs 2026 abgeschlossen (Knicks 4-1 Spurs, letztes Spiel Sa 13.06.). **Praezedenz Ruhetag-Verhalten**: Do 16.07. + Fr 17.07. + Mo 20.07. alle mit 0 Spiele / 0 Tipps / 0 Kombis publiziert - klare Ehrlichkeit statt Fremde-Liga-Fuell-Tipps (Allsvenskan / MLS / Eliteserien / Brasileirao Serie A sind bewusst ausserhalb Fokus-Perimeter, keine 30d-Historie im System). Naechster relevanter Master-Slot voraussichtlich Do/Fr Mitte August wenn Bundesliga/PL/LaLiga wieder starten. Kasse 550 EUR unveraendert (Kasse-Stufe 1 Aufbau-Phase - siehe data/kasse.json). **Statistik-Snapshot Stand 21.07.**: Gesamt 523 Tipps, 287 gewonnen, ROI +4.4%. 30-Tage-Fenster 113 Tipps, ROI -12.7% (durch WM-K.O.-Torschuetzen-Cluster HR07-15-2 fuenf-von-sechs Fehl-Serie + HR07-15-1 Portfolio-Uebertrag-Falle P3-Doppel-Crash weiterhin gedrueckt, natuerliche Erholung erst mit Vereins-Restart) - 30d-ROI-Trigger fuer Kasse-Stufe 2 (>+5% + Kasse >=1000 EUR) doppelt nicht erfuellt, Stufe 1 bleibt aktiv. 18+ / BZgA 0800 1372700.",
  "spiele": [],
  "einzeltipps": [],
  "kombis": [],
  "lessons_angewandt": [
    {
      "id": "ruhetag-ehrlich",
      "titel": "Ruhetag ehrlich als Ruhetag markieren - keine Zwang-Tipps aus Fremden Ligen",
      "quelle": "CLAUDE.md Tonalitaet-Prinzip (Ehrlich, keine Zwang-Tipps) + Praezedenz 2026-07-16 + 2026-07-17 + 2026-07-20",
      "anwendung": "spiele[] leer, einzeltipps[] leer, kombis[] leer. hinweis erklaert Situation transparent inkl. Post-WM-Sommer-Pause-Kalender und Naechster-Slot-Prognose (Mitte August)."
    },
    {
      "id": "fokus-ligen-perimeter",
      "titel": "CLAUDE.md-Fokus-Ligen-Perimeter halten (keine Ausdehnung ohne 30d-Historie)",
      "quelle": "CLAUDE.md Projekt-Zweck (Aktive Sportarten: Fussball WM 2026 + Vereine BL/2BL/PL/LaLiga/Serie A/DFB-Pokal/CL/EL/Conference/Ligue 1/Coppa Italia + NBA Finals)",
      "anwendung": "Allsvenskan (Schweden), Eliteserien (Norwegen), Superettan, MLS (USA), Brasileirao Serie A etc. bewusst nicht getippt trotz Sommer-Aktivitaet. Kein Fremde-Liga-Edge ohne Beobachtungs-Historie im System - siehe Praezedenz 20.07. Ausschluss Oergryte-Djurgaarden."
    },
    {
      "id": "post-wm-sommer-pause-kalender",
      "titel": "Post-WM-Sommer-Pause: naechster relevanter Slot Bundesliga/PL/LaLiga-Start Mitte August",
      "quelle": "CLAUDE.md Aktive Sportarten (Vereine Saison-Pause bis August 2026) + Standard-Wissen Fussball-Saison-Kalender",
      "anwendung": "Ruhetage 20.07.-13.08. sind erwartete Norm. PWA zeigt Ruhetag-Karte statt Fuell-Content. Kein Watchdog-Handstand ins Leere - klare Kommunikation dass Wartezeit bewusst ist."
    },
    {
      "id": "kasse-stufe-1-bei-30d-negativ",
      "titel": "Kasse-Stufe 1 bleibt aktiv solange 30d-ROI negativ ODER Kasse < 1000 EUR",
      "quelle": "CLAUDE.md Einsatz-Limits Stufen-Modell (Stufe 2 nur bei 30d-ROI > +5% UND Kasse >= 1000 EUR)",
      "anwendung": "Beide Trigger nicht erfuellt (Kasse 550 EUR / 30d-ROI -12.7%). Konservativ-Modus bleibt - relevant bei Vereins-Restart Mitte August: nicht sofort in aggressive Einsatz-Range springen sondern erst 2-3 Wochen 30d-Fenster-Recovery abwarten."
    }
  ],
  "_verifikations_report": {
    "erstellt_am": "2026-07-21T17:15:00+02:00",
    "drops": [],
    "downgrades": [],
    "warnungen": [
      "0-Spiele-Ruhetag - keine saison_kontext-Objekte noetig (keine Spiele) und keine Layer-1/2/3-Konflikte moeglich.",
      "Analog Praezedenz 2026-07-16 + 2026-07-17 + 2026-07-20 Ruhetage: klare Ehrlichkeit, keine Fremde-Liga-Ausdehnung (Allsvenskan / MLS / Eliteserien / Brasileirao werden vom Tool nicht getippt weil ohne 30d-Historie und ausserhalb CLAUDE.md-Fokus-Perimeter).",
      "Watchdog-Auslösung: Hauptroutine 16:00 nicht durchgelaufen (data/tipps/2026-07-21.json vor Watchdog-Slot 17:15 nicht vorhanden). Watchdog-Recovery hat 0-Spiele-Ruhetag korrekt reproduziert - identisch zu Master-Pipeline-Verhalten gestern.",
      "Statistik-30d-Fenster ROI -12.7% (leichte Verschlechterung ggue. gestern -11.7% durch Rolling-Window-Verschiebung - WM-K.O.-Torschuetzen-Cluster Fehler bleiben im Fenster, gute alte Tipps rutschen raus) - Kasse-Stufe-1-Konservativ bleibt aktiv (30d-ROI-Trigger fuer Stufe 2 waere >+5% bei Kasse >=1000 EUR, beides nicht erfuellt).",
      "Naechster erwarteter aktiver Master-Slot: DFB-Pokal 1. Runde Fr 14.08.-Mo 17.08.2026 bzw. Bundesliga 1. Spieltag Fr 21.08.-So 23.08.2026 (Sommer-Pause-Rest ca. 24 Tage)."
    ],
    "halluzinations_checks": [
      "WM 2026 Finale Datum So 19.07. verifiziert via data/wm_2026.json + tipps/2026-07-19.json (bereits publiziert ARG vs ESP).",
      "NBA Finals Ende 13.06.2026 (Knicks 4-1 Spurs) aus statistik/lessons/CLAUDE.md-Kalender uebernommen (bestaetigt durch 3x Ruhetag-Praezedenz).",
      "Bundesliga-Saison-Start 21.-23.08.2026 aus CLAUDE.md-Kalender + Standard-DFL-Kalender (DFB-Pokal 1. Runde 14.-17.08. voraus).",
      "Kein Fremde-Liga-Spiel in tipps[] moeglich weil tipps[] leer - Halluzinations-Risiko trivial null.",
      "Kasse-Stand 550 EUR + Statistik-Werte (523 Tipps, ROI +4.4% gesamt, -12.7% 30d, 113 30d-Tipps) aus data/kasse.json + data/statistik.json direkt uebernommen (nicht neu berechnet)."
    ],
    "layer_cross_check": [
      "Layer-1/2/3 alle trivialerweise erfuellt (0 Kombis, 0 Tipps, 0 Spiele).",
      "Anti-Selbstwiderspruchs-Check: nicht anwendbar (keine Tipps).",
      "Markt-Mix-Pflicht (DC-Cap, Star-Ausfall-Backup, Form-Edge-Torschuetzen, NBA-Playoffs-Verbot): nicht anwendbar (keine Spiele).",
      "Beobachtungs-Ligen-Check: nicht anwendbar (keine Spiele in aktiven Ligen)."
    ],
    "kontext_check_status_gesamt": "OK - Ruhetag (Watchdog-Recovery reproduziert Master-Ruhetag-Verhalten)",
    "verifikator_hinweis": "Watchdog-Slot 17:15 Berlin - Hauptroutine 16:00 nicht gelaufen. Ehrlich-Ruhetag-Publikation analog 2026-07-16 + 2026-07-17 + 2026-07-20. Kein Fokus-Liga-Spiel identifiziert (Sommer-Pause aktiv). Naechster erwarteter Master-Slot ab Mitte August bei Vereins-Restart. Kasse-Stufe 1 bleibt aktiv. PWA zeigt Ruhetag-Karte statt Fuell-Content."
  },
  "footer": "18+ · bet365 DE · Hobby-Wetten · Sucht-Hilfe BZgA: 0800 1372700 · Hobby-Tool. Keine Einkommensquelle. Nur setzen was du verlieren kannst. Stress → Pause. Probleme → Hilfe holen."
};
