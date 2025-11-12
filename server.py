import sqlite3
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
from datetime import datetime, timedelta

DB_PATH = "app/database.db"

def parse_datetime(s):
    """Parse datetime string avec ou sans microsecondes"""
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def fetch_data(table_name):
    """
    Récupère les données du jour pour le graphique, une mesure par heure maximale à HH:58.
    L'affichage graphique correspond à l'heure cible (ex : relevé 08:58 → 09:00).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} ORDER BY date ASC")
    rows = cur.fetchall()
    conn.close()

    today_str = datetime.now().strftime("%Y-%m-%d")
    hourly_data = {}

    for row in rows:
        if not row["date"].startswith(today_str):
            continue  # ignorer les autres jours

        dt = parse_datetime(row["date"])
        if dt.minute > 58:
            continue  # ignorer les relevés après HH:58

        # On veut que la mesure soit affichée pour l'heure suivante si proche de HH:58
        display_dt = dt
        if dt.minute >= 58:
            display_dt += timedelta(hours=1)

        hour_key = display_dt.strftime("%Y-%m-%d %H")  # clé unique par heure cible
        hour_label = display_dt.strftime("%H:00")       # label pour le graphique

        # On garde la dernière mesure ≤ HH:58 pour chaque heure cible
        hourly_data[hour_key] = {
            "time": hour_label,  # affichage graphique : HH:00
            "temperature": row["temperature"],
            "pression": row["pression"] if "pression" in row.keys() else None,
            "humidite": row["humidite"] if "humidite" in row.keys() else None
        }

    # trier par heure
    sorted_data = [hourly_data[k] for k in sorted(hourly_data.keys())]
    return sorted_data

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data/today":
            try:
                data = fetch_data("donnee_int")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_error(500, f"Erreur serveur : {e}")
        elif self.path == "/data/today_ext":
            try:
                data = fetch_data("donnee_ext")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_error(500, f"Erreur serveur : {e}")
        else:
            # gérer fichiers statiques
            super().do_GET()

if __name__ == "__main__":
    PORT = 8000
    server = HTTPServer(("0.0.0.0", PORT), MyHandler)
    print(f"🚀 Serveur démarré sur http://10.2.4.32:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⛔ Serveur arrêté par l'utilisateur")
        server.server_close()
