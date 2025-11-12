#!/usr/bin/env python3
"""
Script Python pour lire rtl_433 et insérer dans SQLite

- Lance rtl_433 : sudo rtl_433 -f 868M -g 1000 -A -R 245 -F json
- Récupère time, temperature_C, humidity
- Insère dans la table donnee_ext de app/database.db
"""

import subprocess
import json
import sqlite3
from datetime import datetime
import sys

# -----------------------------
# Configuration
# -----------------------------
DB_PATH = "app/database.db"  # Chemin de ta base
RTL_CMD = [
    "/usr/local/bin/rtl_433",
    "-f", "868M",
    "-g", "48",
    "-A",
    "-R", "245",
    "-F", "json"
]
# -----------------------------

def init_db():
    """Créer la table si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS donnee_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            temperature REAL,
            humidite REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_data(date_str, temperature, humidite):
    """Insérer une ligne dans la table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO donnee_ext (date, temperature, humidite)
            VALUES (?, ?, ?)
        """, (date_str, temperature, humidite))
        conn.commit()
        conn.close()
        print(f"[OK] {date_str} | Temp: {temperature}°C | Hum: {humidite}%")
    except Exception as e:
        print(f"[ERREUR] Insertion BDD : {e}", file=sys.stderr)

def parse_json(line):
    """Extrait les données d'une ligne JSON"""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    date_str = obj.get("time") or datetime.now().isoformat(sep=' ')
    temperature = obj.get("temperature_C") or obj.get("temperature")
    humidite = obj.get("humidity") or obj.get("hum")

    try:
        if temperature is not None:
            temperature = float(temperature)
    except ValueError:
        temperature = None

    try:
        if humidite is not None:
            humidite = float(humidite)
    except ValueError:
        humidite = None

    if temperature is None and humidite is None:
        return None

    return date_str, temperature, humidite

def main():
    print("🚀 Démarrage de rtl_433 et insertion dans SQLite...")
    init_db()

    try:
        proc = subprocess.Popen(
            RTL_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            bufsize=1
        )
    except FileNotFoundError:
        print("❌ rtl_433 non trouvé. Installe-le sur le Pi.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lancement rtl_433 : {e}", file=sys.stderr)
        sys.exit(1)

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            data = parse_json(line)
            if data:
                date_str, temperature, humidite = data
                insert_data(date_str, temperature, humidite)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt manuel du script.")
    except Exception as e:
        print(f"[ERREUR] Boucle principale : {e}", file=sys.stderr)
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
        print("✅ Fin du script.")

if __name__ == "__main__":
    main()
