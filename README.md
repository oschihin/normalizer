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

### 3. API-Key setzen
Lege den Gemini API-Key im Terminal fest:

* **Linux / macOS:**

  ```bash
  export GEMINI_API_KEY="Ihr_API_Key_Hier"
  ```
* **Windows (PowerShell):**

  ```powershell
  $env:GEMINI_API_KEY="Ihr_API_Key_Hier"
  ```
* **Windows (Eingabeaufforderung / CMD):**

  ```cmd
  set GEMINI_API_KEY=Ihr_API_Key_Hier
  ```

### 4. Skript ausführen
Verarbeite die  CSV-Datei:

```bash
python normalize.py input.csv output.csv
```

---

## 🐳 Ausführung im Docker-Container

Wenn du Python nicht lokal installieren möchtest, kannst du das Tool direkt in Docker ausführen.

### 1. Docker-Image bauen

```bash
docker build -t csv-normalizer .
```

### 2. Container ausführen
Gebe den API-Key an und hänge das Verzeichnis für die CSV-Dateien als Volume ein:

* **Linux / macOS:**

  ```bash
  docker run -rm \
    -e GEMINI_API_KEY="Ihr_API_Key_Hier" \
    -v "$(pwd)":/data \
    csv-normalizer /data/input.csv /data/output.csv
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

Du kannst das Verhalten des Skripts über Befehlszeilenparameter steuern:

```bash
python normalize.py --help
```

* `--model`: Bestimmt das zu verwendende Gemini-Modell. Standard ist `gemini-2.5-flash`.
* `--batch-size`: Bestimmt, wie viele CSV-Zeilen pro API-Aufruf verarbeitet werden (Standard: 20). Ein niedrigerer Wert reduziert Speicheranforderungen und vermeidet Timeout-Probleme, ein höherer Wert ist schneller.
