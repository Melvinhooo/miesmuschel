# Pipeline-Prompts + UI-Anleitung Cloud-Routinen

Diese Pipeline trennt das System in **2 Routinen pro Tipp-Slot** (Recherche + Master-Tipps mit interner Verifikation) plus **1 wöchentliche Maintenance**.

## Architektur

```
Mo-Fr:
  10:30 Berlin → miesmuschel-recherche-mo-fr (NEU)        → data/recherche/<datum>.json
  13:30 Berlin → miesmuschel-tipps-mo-fr (Update Prompt)  → data/tipps/<datum>.json
  14:30 Berlin → miesmuschel-watchdog-mo-fr (bestehend)

Sa+So:
  07:00 Berlin → miesmuschel-recherche-sa-so (NEU)        → data/recherche/<datum>.json
  10:00 Berlin → miesmuschel-tipps-sa-so (Update Prompt)
  11:00 Berlin → miesmuschel-watchdog-sa-so (bestehend)

Donnerstag:
  16:30 Berlin → miesmuschel-recherche-wochenende (NEU)   → data/recherche_wochenende/<datum>.json
  18:00 Berlin → miesmuschel-tipps-wochenende (Update)
  19:15 Berlin → miesmuschel-tipps-wochenende-watchdog (bestehend)

Sonntag:
  16:30 Berlin → miesmuschel-recherche-woche (NEU)        → data/recherche_woche/<datum>.json
  18:00 Berlin → miesmuschel-tipps-woche (Update)
  19:15 Berlin → miesmuschel-tipps-woche-watchdog (bestehend)

Wöchentlich Sonntag 21:00 → miesmuschel-maintenance-weekly (NEU)
```

## Prompt-Files

- `recherche_routine.md` — Master-Prompt für die 4 Recherche-Routinen
- `master_tipps_routine.md` — Master-Prompt für die 4 Tipps-Routinen (Plan B: Verifikation als Phase intern, da Task-Tool nicht in Cloud-Routine verfügbar)
- `fussball_analyse.md` + `nba_analyse.md` — Pattern-Knowledge-Referenz für die Master-Tipps-Routine (wird im Prompt referenziert, NICHT als separater Subagent aufgerufen)
- `verifikation.md` — Verifikations-Logik die als interne Phase im Master-Tipps-Prompt eingebaut wird
- `maintenance_routine.md` — Wöchentlicher Health-Check

## UI-Anleitung Cloud-Routinen anlegen (claude.ai/code/routines)

**Wichtig:** Die Anthropic-Cloud-Routines-API ist im v1→v2-Schema-Wechsel und blockt Create/Update via API (Stand 08.05.2026). Manuelle Anlage über UI zwingend.

### Schritt 1: 4 Recherche-Routinen anlegen

URL: https://claude.ai/code/routines

Pro Routine:
- **Name:** `miesmuschel-recherche-<modus>` (mo-fr / sa-so / wochenende / woche)
- **Cron (UTC):**
  - mo-fr: `30 8 * * 1-5` (= 10:30 Berlin MESZ)
  - sa-so: `0 5 * * 6,0` (= 07:00 Berlin)
  - wochenende: `30 14 * * 4` (= 16:30 Berlin Donnerstag)
  - woche: `30 14 * * 0` (= 16:30 Berlin Sonntag)
- **Repository:** github.com/Melvinhooo/miesmuschel
- **Allowed Tools:** Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
- **Modell:** claude-opus-4-7
- **Prompt:** Inhalt von `.github/scripts/subagent_prompts/recherche_routine.md` einfügen, dabei je nach Modus den Output-Pfad anpassen (data/recherche/, data/recherche_wochenende/, data/recherche_woche/)

### Schritt 2: 4 bestehende Tipps-Routinen aktualisieren

Über UI die bestehenden Routinen öffnen und Prompt ersetzen durch Inhalt von `master_tipps_routine.md`.

Routine-IDs (zur Referenz):
- `trig_011ps7wgfJwnLX18nUeZV3nu` = miesmuschel-tipps-mo-fr
- `trig_01MPfUoxZbHYUA4K6CdQb6G3` = miesmuschel-tipps-sa-so
- `trig_01XcqwEKXkNoZorUfnSokY5J` = miesmuschel-tipps-wochenende
- `trig_017GLjns24ZigL3QqK5qmEPp` = miesmuschel-tipps-woche

**Cron unverändert.** Allowed-Tools unverändert (kein Task-Tool nötig).

### Schritt 3: Maintenance-Routine anlegen

- **Name:** miesmuschel-maintenance-weekly
- **Cron (UTC):** `0 19 * * 0` (= Sonntag 21:00 Berlin)
- **Prompt:** Inhalt von `maintenance_routine.md`
- Standard-Tools wie Recherche-Routine

## Test-Strategie

Bevor du die Cloud-Routinen aktivierst, ist im Hauptchat (Claude Code Desktop) ein **manueller Test-Lauf** verfügbar:

1. Test-Recherche für 2026-05-09 manuell ausführen
2. Test-Master-Tipps mit der Recherche-Datei ausführen
3. Verifikation prüft Halluzinationen-Freiheit
4. Wenn alles grün: Cloud-Routinen aktivieren

## Mapper-Integration

Der Schema-Mapper `.github/scripts/fix_schema.py` hat seit 08.05.2026 zwei neue Validators die Recherche-Files konsumieren:

- `validate_recherche_completeness()` — Spiele im Tipps-File müssen im Recherche-File sein
- `validate_spieler_squad_match()` — Spielertor-Tipps müssen Spieler im Squad haben + Position-Check (DM/IV/TW als Stürmer-Tipp = Downgrade)

Beide sind **Bootstrap-tolerant** — wenn Recherche-File fehlt, kein Drop. So funktioniert der Mapper weiter wenn die Recherche-Routine mal ausfällt.
