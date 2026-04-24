# 🐚 Magische Miesmuschel — Bedienungsanleitung

Privates Tipp-Dossier für **bet365 DE** (Fußball + NBA). Hobby-Tool, keine Einnahmequelle.
**18+ · Spielerschutz BZgA: 0800 1372700**

---

## 📂 Was ist wo?

```
Magische Miesmuschel/
├── index.html              ← die App. Per Desktop-Verknüpfung öffnen.
├── CLAUDE.md               ← Regeln, die Claude im Chat respektiert
├── assets/                 ← Styles + JavaScript (nicht anfassen)
├── data/
│   ├── tipps/              ← Tipp-Tage, die Claude im Chat erzeugt
│   ├── ergebnisse/         ← vom Script befüllt nach dem Spieltag
│   ├── lessons.json        ← gesammelte Erkenntnisse
│   ├── config.json         ← dein API-Key (nicht teilen!)
│   └── statistik.js        ← wird automatisch generiert
├── scripts/
│   ├── ergebnisse_holen.bat    ← Doppelklick: Ergebnisse holen
│   └── statistik_berechnen.bat ← Doppelklick: Statistik neu rechnen
└── archiv/                 ← alte HTML-Versionen
```

---

## 🚀 Erste Einrichtung (einmalig, ca. 10 Min)

### 1. Python installieren

Geh auf **https://www.python.org/downloads/** → „Download Python" klicken → Installer starten.

**Wichtig beim Installer:** ✅ „Add Python to PATH" **ankreuzen**, dann „Install Now".

Fertig — Python ist da.

### 2. API-Key für Fußball holen

Geh auf **https://www.football-data.org/client/register** → Name + E-Mail eintragen, einen Moment warten → Key kommt per Mail.

(Kostenlos, Free Tier reicht für das Tool: 10 Anfragen pro Minute, unbegrenzt im Monat.)

### 3. API-Key für NBA holen

Geh auf **https://www.balldontlie.io/** → „Sign up for a free API key" → E-Mail eintragen → Key im Dashboard kopieren.

(Auch kostenlos. Free Tier: 60 Anfragen pro Minute.)

### 4. Keys eintragen

Im Ordner `data/` liegt eine Datei **`config.example.json`**.

1. Kopiere sie und benenne die Kopie um zu **`config.json`** (wichtig: `.example` raus).

   **⚠️ Windows-Falle:** Explorer blendet die Endung `.json` standardmäßig aus.
   Wenn du beim Umbenennen „config.json" tippst, hängt Windows automatisch
   nochmal `.json` dran — die Datei heißt dann unsichtbar `config.json.json`
   und wird nicht gefunden.
   **Lösung:** Explorer → Menü „Ansicht" → „Dateinamenerweiterungen" anhaken,
   dann siehst du die richtige Endung und kannst sauber umbenennen.
   *(Falls das passiert, fängt das Script es beim nächsten Lauf automatisch ab
   und benennt um — aber besser von Anfang an sauber.)*

2. Öffne `config.json` im Editor (Notepad reicht)
3. Trag deine Keys ein:
   ```json
   {
     "football_data_key": "DEIN-LANGER-KEY-HIER",
     "balldontlie_key":   "DEIN-NBA-KEY-HIER"
   }
   ```
4. Speichern, schließen.

Die Datei wird **nicht** in Git commited (steht in `.gitignore`) — sie ist nur auf deinem PC.

---

## 🎯 Tägliche Nutzung

### Tipps für einen neuen Tag bekommen

Einfach **im Claude-Chat** sagen: *„Mach mir die Tipps für heute / morgen / den 23.04."*

Claude schreibt die Datei `data/tipps/YYYY-MM-DD.json` direkt bei dir und benutzt dabei die CLAUDE.md-Regeln + deine bisherige Historie.

### App öffnen

**Doppelklick auf die Verknüpfung „Magische Miesmuschel" auf deinem Desktop.**

Die App hat 5 Tabs:

- **📊 Spiele-Analyse** — Tipps für heute mit Analyse, Quoten, News
- **🎯 Einzeltipps** — die konkreten Picks, nach Qualität sortiert
- **🚀 Risiko-Kombis** — mehrbeinige Wetten mit Gesamtquote
- **📈 Historie** — deine Trefferquote + ROI über die Zeit
- **ℹ️ Regeln** — was in DE erlaubt ist, Einsatz-Limits

### Nach dem Spieltag: Ergebnisse holen

Doppelklick auf **`scripts/ergebnisse_holen.bat`**.

Das passiert:
1. Script prüft Python + `requests` (installiert das Paket automatisch falls es fehlt)
2. Holt alle offenen Tipp-Tage aus `data/tipps/`
3. Ruft für jedes Spiel die API auf, wertet die Tipps aus
4. Schreibt `data/ergebnisse/YYYY-MM-DD.json`
5. Rechnet automatisch die neue Statistik
6. Fertig — schließt erst wenn du eine Taste drückst

Öffne danach die App neu → der „📈 Historie"-Tab zeigt die aktualisierten Kennzahlen.

---

## ❓ Was, wenn ein Spiel nicht gefunden wird?

Manche Wettbewerbe sind **nicht im API-Free-Tier**:

- 🇩🇪 DFB-Pokal
- 🇮🇹 Coppa Italia
- Kleinere Pokalwettbewerbe

Auch **Torschützen-Tipps beim Fußball** können nicht automatisch ausgewertet werden (die freie API liefert nur End- und Halbzeitstände, keine Torschützen).

**Was das Script dann macht:** Der Tipp wird mit `"status": "offen"` markiert, mit einem Kommentar warum (z.B. „DFB-Pokal nicht im API-Free-Tier").

**Was du dann tun kannst:** Die Datei `data/ergebnisse/YYYY-MM-DD.json` im Editor öffnen und von Hand den Status setzen:

```json
{ "tipp_id": "t2", "status": "gewonnen", "gewinn_faktor": 0.70, "kommentar": "manuell: Kane trifft zum 2:0" }
```

Danach einmal `scripts/statistik_berechnen.bat` doppelklicken → fertig.

---

## 💡 Weitere Infos

### Wer macht die Analyse?

**Claude im Chat.** Welche Tipps, welche Kategorien (SAFE/VALUE/WACKEL), welche Kombis — all das bleibt kreative Arbeit im Chat und landet dann als JSON bei dir.

Die Scripts hier machen **nur den stumpfen Teil**:
- API-Abruf der Ergebnisse
- Statistik-Aggregation

Das entlastet dich und gibt Claude eine solide Datenbasis für bessere Empfehlungen am nächsten Tag (aus `data/ergebnisse/` + `data/lessons.json`).

### Lessons Learned

In `data/lessons.json` stehen Erkenntnisse die Claude aus vergangenen Tagen gezogen hat. Die werden im Historie-Tab angezeigt und fließen in zukünftige Empfehlungen ein. Du kannst dort selbst Einträge ergänzen, wenn du magst:

```json
{
  "datum": "2026-04-25",
  "kategorie": "Bundesliga Auswärts",
  "lesson": "Bayern auswärts nach CL-Spielen Woche vorher — oft frisch",
  "bezug_spiel_id": null
}
```

### Wie oft sollte ich das laufen lassen?

- **Ergebnisse holen:** Einmal am Tag nach den Spielen, oder am nächsten Morgen. Reicht.
- **Statistik:** Wird automatisch mit den Ergebnissen berechnet. Nur wenn du `lessons.json` manuell änderst, einmal separat.

---

## 🚨 Spielerschutz

- Hobby-Tool, keine Einnahmequelle
- Nur setzen was du verlieren kannst — **1–2 % der Kasse pro Tipp, Risiko-Kombis 0,1–0,5 %**
- Stress oder Frust? → Pause machen
- Probleme → **BZgA 0800 1372700** (kostenlos, anonym)

---

## 🛠️ Troubleshooting

**„Python nicht gefunden" beim Klick auf die .bat**
→ Python neu installieren mit „Add Python to PATH" aktiviert (siehe Schritt 1 oben).

**„config.json nicht gefunden"**
→ `data/config.example.json` zu `data/config.json` kopieren und Keys eintragen.

**Historie-Tab zeigt „Noch keine Daten"**
→ Du hast noch keine Tipp-Tage abgeschlossen. Lass `ergebnisse_holen.bat` einmal laufen.

**API gibt 429 (Rate Limit)**
→ Du hast in kurzer Zeit zu viele Anfragen abgesetzt. Das Script wartet automatisch 70 Sek und probiert noch mal. Wenn's öfter kommt, einfach nochmal starten.

**Icon fehlt / Chrome-Logo wieder da**
→ Rechtsklick auf Desktop → „Aktualisieren" (F5). Windows cached Icons manchmal.
