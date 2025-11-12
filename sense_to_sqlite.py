#!/usr/bin/env python3
"""
Collecte des données intérieures via Sense HAT et insertion dans SQLite.
Relevés toutes les 50 secondes.
"""

from sense_hat import SenseHat
import sqlite3
from datetime import datetime
import time

DB_PATH = "app/database.db"

def init_db():
    """Créer la table si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS donnee_int (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            temperature REAL,
            pression REAL,
            humidite REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_data(date_str, temperature, pression, humidite):
    """Insérer une ligne dans la table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO donnee_int (date, temperature, pression, humidite)
            VALUES (?, ?, ?, ?)
        """, (date_str, temperature, pression, humidite))
        conn.commit()
        conn.close()
        print(f"[OK] {date_str} | {temperature:.1f}°C | {pression:.1f}hPa | {humidite:.1f}%")
    except Exception as e:
        print(f"[ERREUR] Insertion BDD : {e}")

def main():
    sense = SenseHat()
    init_db()
    print("🚀 Démarrage de la collecte intérieure toutes les 50 secondes...")

    while True:
        try:
            temperature = sense.get_temperature()
            pression = sense.get_pressure()
            humidite = sense.get_humidity()
            date_str = datetime.now().isoformat(sep=' ')
            insert_data(date_str, temperature, pression, humidite)
        except Exception as e:
            print(f"[ERREUR] Lecture Sense HAT : {e}")
        time.sleep(50)  # toutes les 50 secondes

if __name__ == "__main__":
    main()
