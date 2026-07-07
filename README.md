# CSV-Personen-Normalisierer mit Gemini AI

Dieses CLI-Tool und Docker-Setup ermöglicht die Normalisierung und Strukturierung von Personendaten aus CSV-Dateien mittels Google Gemini.

Es teilt Rohdaten (z.B. aus Archivkatalogen) automatisch auf in:
- **Typ**: Natürliche Person, Körperschaft, Familie
- **Vorname & Nachname**
- **Ledigname / Zusatzname** (in Klammern)
- **Geburtsjahr & Sterbejahr**
- **Berufe, Titel & Grade** (als strukturierte Liste)
- **Notizen/Begründungen**

---

## 🚀 Schnellstart (Lokales Python)

### 1. Voraussetzungen
* Python 3.9 oder neuer
* Ein Google Gemini API-Key (von Google AI Studio)

### 2. Installation
Installiere das offizielle Google GenAI SDK:

```bash
pip install -r requirements.txt
```

### 3. Konfiguration (.env-Datei)
Erstelle eine Datei namens `.env` im selben Verzeichnis wie das Skript. Siehe aus Beispiel auch `.env.example`:

```env
GEMINI_API_KEY="[Dein_API_Key_Hier]"
MODEL="gemini-2.5-flash"
```

*Alternativ:* Lege den Gemini API-Key manuell im Terminal fest:

* **Linux / macOS:**
* 
  ```bash
  export GEMINI_API_KEY="Dein_API_Key_Hier"
  ```
* 
* **Windows (PowerShell):**
  
  ```powershell
  $env:GEMINI_API_KEY="Dein_API_Key_Hier"
  ```
* 
* **Windows (Eingabeaufforderung / CMD):**
  
  ```cmd
  set GEMINI_API_KEY=Dein_API_Key_Hier
  ```

### 4. Skript ausführen
Verarbeite deine CSV-Datei (z. B. im Unterordner `data`):
```bash
python normalize.py data/input.csv data/output.csv
```

---

## 🐳 Ausführung im Docker-Container

Wenn du Python nicht lokal installieren möchtest, kannst du das Tool direkt in Docker ausführen.

### 1. Docker-Image bauen
```bash
docker build -t csv-normalizer .
```

### 2. Container ausführen

Da deine Eingabe- und Ausgabedaten im Unterordner `./data` liegen und `.env` im Hauptverzeichnis (Appdir) liegt, gibt es zwei  Möglichkeiten:

#### Option A: Gesamten Hauptordner einbinden (Empfohlen & am einfachsten)
Hierbei bindest du das gesamte Projektverzeichnis nach `/app` im Container ein. Dadurch wird das lokale `.env` sowie der Unterordner `data` im Container sichtbar, und das Skript lädt `.env` automatisch:

* **Linux / macOS:**
  ```bash
  docker run --rm \
    -v "$(pwd)":/app \
    csv-normalizer data/input.csv data/output.csv
  ```
* **Windows (PowerShell):**
  ```powershell
  docker run --rm `
    -v "${PWD}:/app" `
    csv-normalizer data/input.csv data/output.csv
  ```

#### Option B: Nur den `./data` Unterordner einbinden
Du bindest nur das Verzeichnis `./data` ein und übergibst das `.env` im Appdir über den `--env-file` Parameter von Docker:

* **Linux / macOS:**
  
  ```bash
  docker run --rm \
    --env-file .env \
    -v "$(pwd)/data":/app/data \
    csv-normalizer data/input.csv data/output.csv
  ```

* **Windows (PowerShell):**

  ```powershell
  docker run --rm `
    --env-file .env `
    -v "${PWD}/data:/app/data" `
    csv-normalizer data/input.csv data/output.csv
  ```

#### Option C: Direkte Übergabe der Umgebungsvariablen
Gib den API-Key manuell beim Ausführen des Containers an und binde nur den `./data` Ordner ein:

* **Linux / macOS:**
  ```bash
  docker run --rm \
    -e GEMINI_API_KEY="Ihr_API_Key_Hier" \
    -v "$(pwd)/data":/app/data \
    csv-normalizer data/input.csv data/output.csv
  ```

* **Windows (PowerShell):**
  ```powershell
  docker run --rm `
    -e GEMINI_API_KEY="Ihr_API_Key_Hier" `
    -v "${PWD}:/data" `
    csv-normalizer /data/input.csv /data/output.csv
  ```

---

## 🛠️ CLI-Optionen

Sie können das Verhalten des Skripts über Befehlszeilenparameter steuern:

```bash
python normalize.py --help
```

* `--model`: Bestimmt das zu verwendende Gemini-Modell. Standard ist `gemini-2.5-flash`, soll besser in `.env` gesetzt werden.
* `--batch-size`: Bestimmt, wie viele CSV-Zeilen pro API-Aufruf verarbeitet werden (Standard: 10). Ein niedrigerer Wert reduziert Speicheranforderungen und vermeidet Timeout-Probleme, ein höherer Wert ist schneller.
