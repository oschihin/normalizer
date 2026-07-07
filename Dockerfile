# Verwende ein offizielles Python-Image als Basis
FROM python:3.11-slim

# Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# Anforderungen kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Das Skript und eventuelle Beispieldaten in das Arbeitsverzeichnis kopieren
COPY normalize.py .

# Standardbefehl bei Ausführung des Containers
ENTRYPOINT ["python", "normalize.py"]
CMD ["--help"]
