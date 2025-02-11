import paho.mqtt.client as mqtt
import psycopg2
import threading
from datetime import datetime
import re

# Configuration MQTT
ADRESSE_IP = '10.42.0.242'
PORT = 1883
TOPIC = 'test_channel'

# Configuration PostgreSQL
DB_NAME = 'capteurs'
DB_USER = 'postgres'
DB_PASSWORD = 'Xerox@170304'
DB_HOST = 'localhost'  # Modifier si nécessaire
DB_PORT = '5432'

# Connexion à la base de données
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()

# Création de la table si elle n'existe pas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        humidite REAL,
        temperature REAL,
        co2 INTEGER,
        nano_particules INTEGER,
        son INTEGER
    )
''')
conn.commit()

# Fonction pour analyser le message et extraire les données
def parse_message(message):
    pattern = r'humidité\s*:\s*([\d.]+)|temperature\s*:\s*([\d.]+)|co2\s*:\s*(\d+)|nano particules\s*:\s*(\d+)|son\s*:\s*(\d+)'
    matches = re.findall(pattern, message)
    
    data = [None] * 5  # Pour stocker les valeurs dans l'ordre
    for match in matches:
        for i, value in enumerate(match):
            if value:
                data[i] = float(value) if '.' in value else int(value)
    return data

# Fonction appelée lorsqu'un message est reçu
def on_message(client, userdata, msg):
    message = msg.payload.decode()
    timestamp = datetime.now()
    print(f'Message reçu : {message} à {timestamp}')
    
    # Extraction des valeurs
    values = parse_message(message)
    
    # Insertion dans la base de données
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, humidite, temperature, co2, nano_particules, son)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (timestamp, values[0], values[1], values[2], values[3], values[4]))
    conn.commit()

# Initialisation MQTT
client = mqtt.Client()
client.on_connect = lambda c, u, f, r: c.subscribe(TOPIC)
client.on_message = on_message
client.connect(ADRESSE_IP, PORT, 60)

# Écoute des messages MQTT
client.loop_forever()

# Fermer la connexion à la base de données à la fin (jamais atteint avec loop_forever)
cursor.close()
conn.close()
