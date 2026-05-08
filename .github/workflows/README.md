# GitHub Actions Pipeline (Magische Miesmuschel)

## Was diese Workflows machen

Ersatz für die Anthropic-Cloud-Routinen (deren API ist im v1→v2-Schema-Wechsel kaputt).
Laufen via GitHub Actions Cron + claude-code-action mit deinem Max-Plan-OAuth-Token.

## Workflows

| Workflow | Cron | Berlin | Was |
|---|---|---|---|
| `miesmuschel-recherche-mo-fr.yml` | `30 8 * * 1-5` | Mo-Fr 10:30 | Squad/Quoten/Verletzungen für Mo-Fr-Tipps |
| `miesmuschel-recherche-sa-so.yml` | `0 5 * * 6,0` | Sa+So 07:00 | Recherche für Sa+So-Tipps |
| `miesmuschel-recherche-wochenende.yml` | `30 14 * * 4` | Do 16:30 | Recherche für Wochenend-Vorschau |
| `miesmuschel-recherche-woche.yml` | `30 14 * * 0` | So 16:30 | Recherche für Wochen-Vorschau |
| `miesmuschel-tipps-mo-fr.yml` | `30 11 * * 1-5` | Mo-Fr 13:30 | Tipps-Master (ersetzt kaputte Cloud-Routine) |
| `miesmuschel-maintenance.yml` | `0 19 * * 0` | So 21:00 | Wöchentlicher Health-Check |

DST-Hinweis: Bei Wechsel auf MEZ am 25.10.2026 alle Cron +1h.

## Setup (einmalig — User-Aktion)

### 1. OAuth-Token vom Max-Plan erstellen

In Claude Code:
```bash
claude setup-token
```
→ kopiere den OAuth-Token (beginnt mit `sk-ant-oat...` oder ähnlich).

### 2. Token als GitHub Secret setzen

Auf GitHub:
1. Repository öffnen: https://github.com/Melvinhooo/miesmuschel
2. Settings → Secrets and variables → Actions
3. "New repository secret":
   - Name: `CLAUDE_CODE_OAUTH_TOKEN`
   - Value: der Token aus Schritt 1
4. Save

### 3. Existierende Secrets verifizieren

Prüfe dass diese Secrets schon gesetzt sind (für Push-Workflow):
- `VAPID_PRIVATE`
- `PUSH_SUB`

## Test

Nach dem Setup kannst du jeden Workflow manuell triggern:
1. Repository → Actions Tab
2. Workflow auswählen (z.B. "Miesmuschel Recherche Mo-Fr")
3. "Run workflow" → Branch: main → "Run workflow"

## Was bestehen bleibt (Cloud-Routinen)

Diese Cloud-Routinen funktionieren noch und brauchen keinen Ersatz:
- Auswertung daily (08:00 Berlin)
- Tipps Sa-So (Cloud-Routine, läuft normal)
- Tipps Wochenende (Cloud-Routine)
- Tipps Woche (Cloud-Routine)
- Watchdogs (Cloud-Routinen)

→ NUR Mo-Fr-Tipps + alle 4 Recherche-Routinen + Maintenance laufen via GitHub Actions.

## Was im Repo dazu gehört

- `.github/scripts/subagent_prompts/recherche_routine.md` — Master-Prompt für Recherche
- `.github/scripts/subagent_prompts/master_tipps_routine.md` — Master-Prompt für Tipps
- `.github/scripts/subagent_prompts/fussball_analyse.md` + `nba_analyse.md` — Pattern-Knowledge
- `.github/scripts/subagent_prompts/verifikation.md` — Halluzinations-Schutz
- `.github/scripts/subagent_prompts/maintenance_routine.md` — Health-Check
- `.github/scripts/fix_schema.py` — Mapper mit Validators

## Token-Budget

OAuth-Token vom Max-Plan zählt gegen Plan-Quota — keine Extra-Kosten wenn unter Limit.

Pro Tag laufen 1-2 Workflows à ~30 Min Token-Last (~50-150k Tokens).
Geschätzt: ~5-10% Max-Plan-Quota pro Tag bei Vollbetrieb.

Bei Quota-Knappheit: claude_args `--max-turns` reduzieren oder einzelne Workflows pausieren via `enabled: false` (workflow_dispatch nur).
