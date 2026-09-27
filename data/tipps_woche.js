// Auto-generiert
window.__MIESMUSCHEL_TIPPS_WOCHE = {
  "datum": "2026-09-28",
  "erstellt_am": "2026-09-27T18:05:00+02:00",
  "modus": "woche",
  "anker_montag": "2026-09-28",
  "fenster_ende_sonntag": "2026-10-04",
  "safety_net_backstop": false,
  "hinweis": "🐚 Wochen-Vorschau Mo 28.09. bis So 04.10.2026 (So-Slot 18:00 Berlin, Saison 2026/27, Kasse 1000€ / Stufe 1). Ehrlich: NULL Spiele im Fenster fuer die aktiven Vereins-Wettbewerbe unserer Whitelist. Grund: XL-FIFA-Laenderspielpause 2026/27 vom 21.09. bis 06.10.2026 (16 Tage am Stueck - Nations League MD1 24.-27.09., MD3 01.-03.10., MD4 04.-06.10.). Recherche-Ergebnisse: Bundesliga MW4 lief 18.-20.09., MW5 erst Fr 09.10.-So 11.10. (Do 08.10. ausserhalb Fenster); Premier League MW5 durch 19.-20.09., MW6 erst Fr 09.10.-So 11.10. (Klassiker Liverpool-ManCity, ManUtd-Tottenham, Arsenal-Leeds); LaLiga J6 midweek 22.-24.09. durch (letzte Woche gespielt), J7 erst 10.-12.10.; Serie A g5 durch 19.-21.09., g6 erst Sa 10.10. (Genoa-Fiorentina, Inter-Parma, Napoli-Frosinone); Ligue 1 J5 durch 19.-21.09., J6 erst Fr 09.10.-So 11.10.; 2. Bundesliga MD6 durch 18.-20.09. (u.a. Wolfsburg 5:1 Darmstadt, Karlsruhe 0:1 Nuernberg, Hannover 2:1 Bochum), MD7 erst Sa 10.10. (u.a. Nuernberg-Wolfsburg 20:30 laut kicker); DFB-Pokal 2. Runde erst 27.-28.10. (Auslosung 05.09., u.a. Magdeburg-Bayern); Coppa Italia R16 mit Serie-A-Teams erst 02.12.; Champions League MD2 13.-14.10. (u.a. Arsenal-Lille, Atletico-ManUtd, Inter-Brugge, Galatasaray-Barca, ManCity-PSG); Europa League MD2 15.10.; Conference League MD1 (Ligaphase-Start) 15.10.; Copa del Rey R1 28.10.; Coupe de France Bundesliga-Aequivalent-Runde Okt/Nov (Ligue-1-Teams noch nicht dabei); EFL Cup R4 in der Woche 26.-29.10. (u.a. Fleetwood-Arsenal, Liverpool-Chelsea, ManCity-Brighton laut Auslosung 16.09.); FA Cup Emirates 3rd Qualifying Round Sa 03.10. - fallen alle unter Non-League und Beobachtungs-Liga-Filter (keine Vereinssaison-Whitelist). Kein Supercup in diesem Zeitfenster (Trophee des Champions erst Januar, Supercopa/Supercoppa/Community Shield lange durch, UEFA Super Cup war Mitte August). Nations League steht per CLAUDE.md-Regel 'Aktive Sportarten' NICHT in unserer Whitelist (nur Vereins-Wettbewerbe + WM/EM-Turniere), deshalb keine Spielansetzungen wie Deutschland-Griechenland 03.10. oder Portugal-Danemark 01.10. hier drin. Ergebnis: ehrliches leeres Wochen-Dossier statt erfundener Tipps - Notfall-Fallback-Regel aus master_tipps_routine.md greift ('lieber ein kleines ehrliches Dossier als gar keins'). Naechstes echtes Wochen-Dossier: So 04.10. abends fuer die Woche Mo 05.10.-So 11.10. mit vollem Restart aller Ligen. Wochenend-Dossier davor: Do 08.10. fuer Fr 09.10.-So 11.10. Kasse-Stand 1000€ / Stufe 1 aktiv (rolling 30 Tage ROI +83.1% ist stark, aber stufe_2_freigeschaltet noch false laut kasse.json - Saison-Edge muss erst manuell freigeschaltet werden) - bleibt in diesem Break unangetastet.",
  "spiele": [],
  "einzeltipps": [],
  "kombis": [],
  "lessons_angewandt": [
    "Zeitfenster-Hartregel (CLAUDE.md 22.08.2026): nur Anstoss-Tage Mo 28.09.-So 04.10., alle Ligen live geprueft - keine Whitelist-Spiele im Fenster.",
    "Notfall-Fallback aus master_tipps_routine.md: leeres Dossier ist ein gueltiges Ergebnis, wenn keine Spiele im Fenster liegen. Erfinden waere schaedlicher als Schweigen.",
    "Konsistenz mit Wochenend-Safety-Net vom Do 26.09.: gleiche Datenlage (FIFA-Pause 21.09.-06.10.), gleiche Konsequenz.",
    "CLAUDE.md Aktive-Sportarten-Whitelist: Nations-League-MDs 3/4 (01.-03.10. bzw. 04.-06.10.) werden explizit NICHT aufgenommen - Vereinssaison-Modus statt Nationalteam-Modus.",
    "CLAUDE.md Supercup-Sonderregel: fuer diesen Zeitraum kein Supercup terminiert - Trophee des Champions Januar in Riad, Supercopa/Supercoppa/Community Shield laengst gespielt, UEFA Super Cup war 13.08.",
    "CLAUDE.md Kasse-Regel: Stufe 1 aktiv bis stufe_2_freigeschaltet=true - obwohl rolling-30-Tage-ROI +83.1% laut statistik.json den Threshold reisst, wartet Freischaltung auf Melvi's manuelles Toggle."
  ],
  "_verifikations_report": {
    "erstellt_am": "2026-09-27T18:05:00+02:00",
    "drops": [],
    "downgrades": [],
    "warns": [],
    "lessons_generiert": [
      "Wochen-Vorschau in FIFA-Pause: Recherche muss beide MD-Fenster (MD3 + MD4) und alle grossen Liga-Restart-Termine (09.-11.10. + 13.-15.10.) explizit abklopfen, bevor 'leer' als Ergebnis akzeptiert wird - so wie hier fuer 5 grosse Ligen + 4 UEFA-Wettbewerbe + 4 nationale Pokale einzeln verifiziert."
    ],
    "note": "Kein Halluzinations-Risiko: spiele[] = [] verhindert Kader-/Trainer-/Markt-Widersprueche. Kein Downgrade noetig, weil kein Tipp gesetzt wurde."
  },
  "footer": "18+ · BZgA Gluecksspielsucht-Hotline: 0800 1372700 · Hobby-Tool. Keine Einkommensquelle. Nur setzen was du verlieren kannst. Stress -> Pause. Probleme -> Hilfe holen."
};
