import paho.mqtt.client as mqtt
import csv
import threading
from datetime import datetime
import re


ADRESSE_IP = '10.42.0.242'
PORT = 1883
TOPIC = 'test_channel'


timestamps = []
humidite = []
temperature = []
co2 = []
nano_particules = []
son = []


def parse_message(message):
    pattern = r'humidité\s*:\s*([\d.]+)|temperature\s*:\s*([\d.]+)|co2\s*:\s*(\d+)|nano particules\s*:\s*(\d+)|son\s*:\s*(\d+)'
    matches = re.findall(pattern, message)
    
    data = [None] * 5 
    for match in matches:
        for i, value in enumerate(match):
            if value:
                data[i] = float(value) if '.' in value else int(value)
    return data


def on_message(client, userdata, msg):
    message = msg.payload.decode()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'Message reçu : {message} à {timestamp}')
    
    timestamps.append(timestamp)
    
    
    values = parse_message(message)
    humidite.append(values[0])
    temperature.append(values[1])
    co2.append(values[2])
    nano_particules.append(values[3])
    son.append(values[4])


def save_data_to_csv():
    if timestamps:
        with open('mqtt_data.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            if file.tell() == 0:
                writer.writerow(["Timestamp", "Humidité", "Température", "CO₂", "Nano Particules", "Son"])
            for i in range(len(timestamps)):
                writer.writerow([
                    timestamps[i],
                    humidite[i],
                    temperature[i],
                    co2[i],
                    nano_particules[i],
                    son[i]
                ])
        # Efface les données après l'enregistrement
        timestamps.clear()
        humidite.clear()
        temperature.clear()
        co2.clear()
        nano_particules.clear()
        son.clear()
    threading.Timer(60, save_data_to_csv).start()


client = mqtt.Client()
client.on_connect = lambda c, u, f, r: c.subscribe(TOPIC)
client.on_message = on_message
client.connect(ADRESSE_IP, PORT, 60)


save_data_to_csv()


client.loop_forever()
