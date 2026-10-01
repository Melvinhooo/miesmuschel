// Auto-generiert
window.__MIESMUSCHEL_TIPPS_WOCHENENDE = {
  "datum": "2026-10-03",
  "erstellt_am": "2026-10-01T18:15:00+02:00",
  "modus": "wochenende",
  "safety_net_backstop": false,
  "fenster": {
    "samstag": "2026-10-03",
    "sonntag": "2026-10-04"
  },
  "hinweis": "🐚 Wochenend-Vorschau Sa 03.10. + So 04.10.2026 (Do-Slot 18:00 Berlin, Saison 2026/27). Ergebnis nach Nachrecherche: NULL Spiele im Fenster fuer die aktiven Vereins-Ligen und Pokale unserer Whitelist. Grund: wir sind weiterhin mitten in der MERGED FIFA-Laenderspielpause 2026/27 vom 21.09. bis 06.10.2026 (16 Tage am Stueck, siehe Bundesliga.com + Spox + Sportschau). Bundesliga MW4 lief 18.-20.09., MW5 startet erst Fr 09.10. (BVB-Bremen 20:30) und laeuft Sa 10.10. + So 11.10. Premier League MW5 lief 19.-20.09., MW6 erst Sa 10.10. (Arsenal-Leeds, Chelsea-Bournemouth u.a.). LaLiga J6 erst nach dem Break, Serie A 6^ giornata am 10.-11.10. (Napoli-Frosinone u.a.), Ligue 1 J6 am 10.-11.10. 2. Bundesliga MW7 am 09.-11.10. (u.a. Nuernberg-Wolfsburg Sa 20:30, Hertha-Fuerth, Bochum-Bielefeld, St.Pauli-Karlsruhe So). CL/EL/Conference MD1 lief 16.-18.09., CL-MD2 erst 13.-14.10., EL-MD2 15.10., Conference-MD2 22.10. DFB-Pokal R2 am 27.-28.10., EFL-Cup R4 w/c 26.10., Coppa Italia R16 Serie-A-Teams ab 02.12., Copa del Rey R1 28.10., Coupe de France R7 Nov. FA Cup am Sa 03.10. nur Third Round Qualifying (Non-League, keine Whitelist). Kein Supercup dieses WE (Franz-Beckenbauer-Supercup war 22.08., FA Community Shield 10.08., Supercopa Espana + Supercoppa Italiana laufen in der Winterpause, UEFA Super Cup war Aug, Trophee des Champions Jan). Was am WE laeuft: Nations League MD3 (01.-03.10.) und MD4 (04.-06.10.) - z.B. Kroatien-England, Spanien-Tschechien, Deutschland-Serbien - aber Nations League steht nicht in unserer Whitelist (nur Vereins-Wettbewerbe + Turniere WM/EM, siehe CLAUDE.md 'Aktive Sportarten'). Deshalb ehrlich ein leeres Wochenend-Dossier statt erfundener Tipps - Notfall-Fallback aus master_tipps_routine.md greift. Naechstes echtes Wochenend-Dossier: Do 08.10. (Vorschau auf Bundesliga MW5 + PL MW6 + Serie A / LaLiga / Ligue 1 J6 + 2.BL MW7). Kasse-Stand 1000€ / Stufe 1 aktiv (Saison-eigener Edge noch nicht bestaetigt - rolling 30 Tage ROI zwar bei +72.8%, aber grossteils aus WM-Vorperiode, stufe_2_freigeschaltet=false) - Kasse bleibt an diesem WE unangetastet. 18+ · BZgA Gluecksspielsucht-Hotline: 0800 1372700.",
  "spiele": [],
  "einzeltipps": [],
  "kombis": [],
  "lessons_angewandt": [
    "Zeitfenster-Hartregel (22.08.2026): Wochenend-Dossier deckt genau Sa+So ab. Kein Nations-League-Nachschub aus Do 01.10. / Fr 02.10. / Mo 05.10. reingeschleppt.",
    "Notfall-Fallback (CLAUDE.md / master_tipps_routine.md 'Notfall-Fallback'): lieber ehrlich leer als erfunden. Nichts halluzinieren - fehlende Daten als leer setzen und im Hinweis begruenden.",
    "Whitelist-Disziplin: Nations League ist Nationalmannschafts-Wettbewerb, steht nicht in 'Aktive Sportarten' (nur Vereine + Turniere WM/EM) -> keine Tipps darauf, auch wenn Spiele stattfinden.",
    "Break-Fortsetzung (Lehre 2026-09-26): die merged FIFA-Pause 21.09.-06.10. deckt BEIDE Oktober-Wochenenden ab, nicht nur das September-Ende. Erst ab 09.-11.10. gibt es wieder Vereinsfussball in den Whitelist-Ligen.",
    "Keine Supercups geprueft und keine im Fenster: alle sechs Pflicht-Supercups (Franz-Beckenbauer-Supercup, FA Community Shield, Supercopa Espana, Supercoppa Italiana, Trophee des Champions, UEFA Super Cup) liegen nachweislich nicht auf 03.-04.10.2026."
  ],
  "_verifikations_report": {
    "erstellt_am": "2026-10-01T18:15:00+02:00",
    "trigger": "Wochenend-Vorschau Do-Slot 18:00 Berlin. Nachverifikation per WebSearch da football-data.org API in der Routine-Sandbox nicht erreichbar (403 Forbidden am Egress-Proxy).",
    "drops": [],
    "downgrades": [],
    "warns": [
      {
        "art": "leerer_slate",
        "spiel_id": null,
        "details": "Merged FIFA-Laenderspielpause 21.09.-06.10.2026 - alle Top-5-Ligen + 2.BL + Europapokal-Ligaphase pausieren, kein Whitelist-Wettbewerb am 03.-04.10. Verifiziert per WebSearch: Bundesliga MW5 09.-11.10. (DFL/Spox/Sportschau bestaetigt), PL MW6 ab 10.10. (NBC/premierleague.com), Serie A/LaLiga/Ligue 1 wieder ab 10.-11.10., 2.BL MW7 09.-11.10. (kicker.de), DFB-Pokal R2 27.-28.10., FA Cup am 03.10. nur Qualifikation Non-League, kein Supercup im Fenster. Nations League MD3+4 im Fenster, aber nicht in der Whitelist."
      },
      {
        "art": "api_block",
        "spiel_id": null,
        "details": "football-data.org vom Egress-Proxy mit 403 geblockt (recentRelayFailures bestaetigt). Routine ist auf WebSearch/WebFetch ausgewichen. Fuer die naechste echte Vorschau (08.10.) ggf. Infra-Routing pruefen - andernfalls bleibt WebSearch der primaere Pfad fuer Spielplan-Verifikation."
      }
    ],
    "lessons_generiert": [],
    "quellen": [
      "https://www.spox.com/fussball/news/bundesliga-saison-2026-27-warum-ist-zwischen-september-und-oktober-drei-wochen-laenderspielpause/blt405fb3fe17574750",
      "https://anstosszeiten.de/bundesliga/spieltag-5/",
      "https://www.ruhrnachrichten.de/service/bundesliga-fussball-fuenfter-spieltag-saison-2026-27-partien-mannschaften-uebertragung-w1251490-2002238953/",
      "https://www.premierleague.com/en/news/4689113/when-are-the-international-breaks-for-202627",
      "https://www.sportschau.de/fussball/ab-montag-fast-drei-wochen-laenderspiele,laenderspiele-fenster-neu-100.html",
      "https://www.kicker.de/2-bundesliga/spieltag/2026-27/7",
      "https://www.si.com/soccer/why-three-weeks-until-next-premier-league-games",
      "https://www.si.com/soccer/2026-27-carabao-cup-draw-fixtures-results-guide-each-round",
      "https://www.thefa.com/competitions/thefacup/round-dates",
      "https://en.wikipedia.org/wiki/2026_Supercopa_de_Espa%C3%B1a_final",
      "https://en.wikipedia.org/wiki/2025%E2%80%9326_Supercoppa_Italiana"
    ]
  },
  "footer": "18+ · bet365 DE · Hobby-Wetten · BZgA Gluecksspielsucht-Hotline: 0800 1372700"
};
