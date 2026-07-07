#!/usr/bin/env python3
"""
CSV-Personen-Normalisierer mit Gemini AI
Dieses Skript liest eine CSV-Datei mit Rohdaten zu Personennamen,
normalisiert die Informationen mithilfe der Gemini API und speichert
die strukturierten Daten in einer neuen CSV-Datei.

Nutzung:
    python normalize.py <input_csv> <output_csv> [options]
"""

import os
import sys
import csv
import json
import argparse
from typing import List, Dict, Any

# Wir importieren das offizielle google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Fehler: Das 'google-genai' Paket ist nicht installiert.", file=sys.stderr)
    print("Bitte installieren Sie es mit: pip install google-genai", file=sys.stderr)
    sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Strukturiere und normalisiere Personendaten in CSV-Dateien mit Gemini AI."
    )
    parser.add_argument(
        "input_file", 
        help="Pfad zur Eingabe-CSV-Datei (Spalten müssen mindestens 'person' und 'name' enthalten)"
    )
    parser.add_argument(
        "output_file", 
        help="Pfad zur Ausgabe-CSV-Datei, in der die strukturierten Daten gespeichert werden"
    )
    parser.add_argument(
        "--model", 
        default="gemini-2.5-flash",
        help="Das zu verwendende Gemini-Modell (Standard: gemini-2.5-flash)"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=20,
        help="Anzahl der Zeilen pro API-Anfrage (Standard: 20)"
    )
    return parser.parse_args()


def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Liest die Eingabe-CSV und gibt eine Liste von Dictionaries zurück."""
    if not os.path.exists(file_path):
        print(f"Fehler: Datei '{file_path}' wurde nicht gefunden.", file=sys.stderr)
        sys.exit(1)
        
    entries = []
    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            # Erkennen des Dialekts (Trennzeichen , oder ;)
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
            
            # Falls Sniffer fehlschlägt, standardmäßig Komma oder Semikolon nutzen
            reader = csv.DictReader(f, dialect=dialect)
            
            # Überprüfen, ob die benötigten Spalten existieren
            headers = reader.fieldnames or []
            normalized_headers = {h.lower().strip('" '): h for h in headers}
            
            person_col = None
            name_col = None
            
            if 'person' in normalized_headers:
                person_col = normalized_headers['person']
            elif 'id' in normalized_headers:
                person_col = normalized_headers['id']
                
            if 'name' in normalized_headers:
                name_col = normalized_headers['name']
                
            if not person_col or not name_col:
                # Fallback: Erste Spalte als ID, zweite als Name annehmen
                if len(headers) >= 2:
                    person_col = headers[0]
                    name_col = headers[1]
                    print(f"Hinweis: Spalten 'person'/'name' nicht eindeutig gefunden. Nutze '{person_col}' als ID und '{name_col}' als Name.", file=sys.stderr)
                else:
                    print(f"Fehler: CSV benötigt mindestens zwei Spalten (z.B. 'person' und 'name'). Gefundene Spalten: {headers}", file=sys.stderr)
                    sys.exit(1)
            
            for row in reader:
                entries.append({
                    "id": row.get(person_col, "").strip(),
                    "name": row.get(name_col, "").strip()
                })
    except Exception as e:
        print(f"Fehler beim Lesen der CSV-Datei: {e}", file=sys.stderr)
        sys.exit(1)
        
    return entries


def create_prompt(batch: List[Dict[str, str]]) -> str:
    """Erstellt den Prompt für die Strukturierung."""
    prompt = """Du bist ein Experte für Archivwesen, historische Namensdatenbanken und Personendaten-Normalisierung.
Normalisiere die folgende Liste von Personendaten-Einträgen aus einem Archivkatalog. Jede Zeile hat ein 'id' und ein 'name' (Rohname).

Teile die Informationen präzise wie folgt auf:
1. 'id': Behalte die originale ID unverändert bei.
2. 'rawName': Behalte den originalen Rohnamen unverändert bei.
3. 'type': Bestimme den Typ:
   - "natürliche Person" (wenn es eine einzelne Person ist, z.B. "Aemmer, Friedrich (1867-1934), Regierungsrat" oder "Aecker, Elisabeth (1879-)")
   - "Körperschaft" (wenn es eine Organisation, Firma, Verein, Stiftung, Kommission, etc. ist, z.B. "Aktienmühle Basel und Augst", "Aktiengesellschaft Adolf Remund", "Aeneas-Silvius-Stiftung", "Aegerter & Bosshardt (Ingenieurbüro)")
   - "Familie" (wenn es sich um eine Familie handelt, z.B. "Familie Aegerter", "Aeschbach (Familie)")
   - "unbekannt" (wenn unklar)
4. 'firstName': Vorname der Person (nur bei "natürliche Person", sonst leer lassen). Bei "Aemmer, Friedrich" ist der Vorname "Friedrich".
5. 'lastName': Nachname oder Familienname. Bei "Aemmer, Friedrich" ist der Nachname "Aemmer". Bei Körperschaften oder Familien trage den gesamten Namen hier ein.
6. 'maidenName': Ledigname oder Zusatzname in Klammern (oft nachgestellt oder eingeklammert, z.B. "Brillinger" bei "Aeschlimann, Alexander (Brillinger)", "Haslhofer" bei "Aigner, Marie (Haslhofer)", "Gerter" bei "Aegerter, Elisabeth (Gerter)", "Bayde" bei "Aegerter, Fritz (Bayde)"). Falls kein Zusatzname/Ledigname vorliegt, leer lassen.
7. 'birthYear': Geburtsjahr als Ganzzahl (z.B. 1867 bei "(1867-1934)", 1900 bei "(1900-)"). Falls kein Geburtsjahr vorhanden ist, setze null oder lass es weg.
8. 'deathYear': Sterbejahr als Ganzzahl (z.B. 1934 bei "(1867-1934)"). Falls kein Sterbejahr vorhanden ist (z.B. bei "(1900-)"), setze null oder weglassen.
9. 'professions': Eine Liste von Berufen, Ämtern, Titeln oder akademischen Graden (z.B. "Regierungsrat", "Notar", "Prof.", "Dr.", "PD Dr."). Bereinige diese und trenne sie in einzelne Einträge auf (z.B. ["Regierungsrat"], ["Prof.", "Dr.", "Notar"]).
10. 'notes': Eine kurze Erklärung oder Begründung für die Normalisierung (z.B. "Natürliche Person mit Geburtsjahr und Beruf").

Hier ist die Liste der zu normalisierenden Einträge:
"""
    prompt += json.dumps(batch, ensure_ascii=False, indent=2)
    return prompt


def normalize_batch(client: genai.Client, model: str, batch: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Sendet einen Batch an Gemini und liefert die strukturierten Ergebnisse zurück."""
    prompt = create_prompt(batch)
    
    # Definieren des erwarteten JSON-Schemas für die strukturierte Ausgabe
    # Wir verwenden die offizielle API-Definition des google-genai SDKs
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "results": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "rawName": {"type": "STRING"},
                        "type": {
                            "type": "STRING", 
                            "description": "Der Typ: 'natürliche Person', 'Körperschaft', 'Familie' oder 'unbekannt'"
                        },
                        "firstName": {"type": "STRING", "nullable":True},
                        "lastName": {"type": "STRING", "nullable": True},
                        "maidenName": {"type": "STRING", "nullable": True},
                        "birthYear": {"type": "INTEGER", "nullable": True},
                        "deathYear": {"type": "INTEGER", "nullable": True},
                        "professions": {
                            "type": "ARRAY",
                            "items": {"type": "STRING", "nullable": True}
                        },
                        "notes": {"type": "STRING", "nullable": True}
                    },
                    "required": ["id", "rawName", "type", "firstName", "lastName", "maidenName", "professions", "notes"]
                }
              }
        },
        "required": ["results"]
    }
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,  # Niedrige Temperatur für deterministische Ergebnisse
            ),
        )
        
        data = json.loads(response.text)
        return data.get("results", [])
    except Exception as e:
        print(f"Fehler bei der API-Normalisierung für einen Batch: {e}", file=sys.stderr)
        # Fallback im Fehlerfall: Gib leere strukturierte Zeilen zurück
        fallback_results = []
        for item in batch:
            fallback_results.append({
                "id": item["id"],
                "rawName": item["name"],
                "type": "unbekannt",
                "firstName": "",
                "lastName": "",
                "maidenName": "",
                "birthYear": None,
                "deathYear": None,
                "professions": [],
                "notes": f"Fehler bei API-Verarbeitung: {str(e)}"
            })
        return fallback_results


def write_csv(file_path: str, data: List[Dict[str, Any]]):
    """Schreibt die strukturierten Ergebnisse in eine neue CSV-Datei."""
    fieldnames = [
        "person", 
        "raw_name", 
        "type", 
        "first_name", 
        "last_name", 
        "maiden_name", 
        "birth_year", 
        "death_year", 
        "professions", 
        "notes"
    ]
    
    try:
        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for item in data:
                # Professions in eine kommagetrennte Liste umwandeln
                professions_str = ", ".join(item.get("professions", []))
                
                writer.writerow({
                    "person": item.get("id", ""),
                    "raw_name": item.get("rawName", ""),
                    "type": item.get("type", "unbekannt"),
                    "first_name": item.get("firstName", ""),
                    "last_name": item.get("lastName", ""),
                    "maiden_name": item.get("maidenName", ""),
                    "birth_year": item.get("birthYear") if item.get("birthYear") is not None else "",
                    "death_year": item.get("deathYear") if item.get("deathYear") is not None else "",
                    "professions": professions_str,
                    "notes": item.get("notes", "")
                })
        print(f"Erfolgreich gespeichert in: {file_path}")
    except Exception as e:
        print(f"Fehler beim Schreiben der Ausgabedatei: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_arguments()
    
    # API-Key abrufen
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Fehler: Die Umgebungsvariable GEMINI_API_KEY ist nicht gesetzt.", file=sys.stderr)
        print("Bitte setzen Sie diese mit: export GEMINI_API_KEY='Ihr_Key_Hier'", file=sys.stderr)
        sys.exit(1)
        
    print("Initialisiere Gemini API Client...")
    client = genai.Client(api_key=api_key)
    
    print(f"Lese Eingabedatei '{args.input_file}'...")
    entries = read_csv(args.input_file)
    total_entries = len(entries)
    print(f"{total_entries} Einträge geladen.")
    
    normalized_results = []
    
    # Aufteilung in Batches
    batch_size = args.batch_size
    for i in range(0, total_entries, batch_size):
        batch = entries[i:i+batch_size]
        current_batch_num = (i // batch_size) + 1
        total_batches = (total_entries + batch_size - 1) // batch_size
        
        print(f"Verarbeite Batch {current_batch_num}/{total_batches} ({len(batch)} Einträge)...")
        
        results = normalize_batch(client, args.model, batch)
        normalized_results.extend(results)
        
    print(f"Normalisierung abgeschlossen. Schreibe {len(normalized_results)} Zeilen in '{args.output_file}'...")
    write_csv(args.output_file, normalized_results)
    print("Fertig!")


if __name__ == "__main__":
    main()
