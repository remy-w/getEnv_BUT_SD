import paho.mqtt.client as mqtt
import pandas as pd
import numpy as np
import datetime as dt
from lib.buttonLED import buttonLED
from lib.sensorSound import sensorSound
from lib.sensorDHT import sensorDHT
from lib.ledstick import ledStick
from lib.buzzer import buzzer
from lib.sensorAirquality import sensorAirquality
from lib.sensorPIR import sensorPIR

class gateway:
	def __init__(self):
		print("Initialisation de la passerelle")

		#Initialisation de tous les capteurs
		self.button_led_sensor = buttonLED.GroveButtonLed(6,5)
		self.capteur_sensor_son = sensorSound.GroveSoundSensor(0)
		self.capteur_humidite_temp = sensorDHT.GroveDHTSensor(26)
		self.capteur_co2_nano = sensorAirquality.GroveAirQualitySensor()
		self.capteur_mouvement = sensorPIR.GrovePirMotionSensor(18)

		# Initialisation de tous les actionneurs
		self.led_stick = ledStick.GroveLedStick(12,10)
		self.buzzer = buzzer.GroveBuzzer(22)

		# Initialisation des variables qui vont sauvegarder les données des capteurs
		self.humidite = 0
		self.temp = 0
		self.mouvement = 0
		self.nano = 0
		self.co2 = 0
		self.son = 0
		self.bouton_relache = 0

		# Initialisation du buzzer
		self.isBuzzer = 0
		self.liste_buzzer_auto = []
		self.buzzer_temp = 0
		self.buzzer_hum = 0
		self.buzzer_co2 = 0
		self.buzzer_nano = 0
		self.buzzer_son = 0

		# Initialisation des variables état (graphe état) et i pour itérer dans les boucles
		self.etat = 0
		self.i = 0
		self.j = 0

		# Initialisation de liste de nombre qui sont nos valeurs réferences pour l'affiche des LED & couleurs
		self.humidite_seuil = [30,60]
		self.temp_seuil = [13, 16, 23, 26]
		self.son_seuil = [200,400,500,750]
		self.co2_seuil = [600,800,1000,1500]
		self.nano_seuil = [221,661,1431,2201]

		# Initialisation des variables pour activer le mode jour/nuit
		self.horaire = dt.datetime.now().time()
		print(self.horaire)
		self.date_jour = dt.datetime.now()
		self.horaire_ouverture = dt.time(7,0,0)
		self.horaire_fermeture = dt.time(19,0,0)
		self.tmp_actuel = 0
		self.premier_temps = 0
		self.seconds_debut = 0
		#self.data = []

		# Initialisation de liste utile pour ajouter des données brutes qui seront agrégés
		self.liste_humidite = []
		self.liste_temperature = []
		self.liste_co2 = []
		self.liste_nano_particules = []
		self.liste_son = []


		# crée une liste pour stocker les horaires (rémy)
		self.liste_horaire = []

		#self.liste_time = []

		#Initialisation des variables saisies dans le csv
		self.avg_humidite = 0
		self.avg_temperature = 0
		self.avg_son = 0
		self.avg_co2 = 0
		self.avg_nano = 0

		# Crée un fichier csv de sauvegarde des données
		with open("all_data.csv", "w") as f:
			f.write('date;heure;temperature;humidite;co2;nano_particules;bruit\n')
		f.close()

		# Initialisation du statut d'écriture du fichier (toutes les minutes)
		self.ecriture_fichier = False


		# client mqtt
		print("tentative mqtt")
		self.client = mqtt.Client()
		self.client.on_connect = on_connect
		self.client.on_publish = on_publish
		self.client.connect("10.42.0.242", 1883, 60)
		self.client.loop_start()




	def inputUpdate(self):

		#print("Mise à jour des entrées")

		# Récupère valeurs des capteurs
		self.capteur_humidite_temp.getRawSensorValue()
		self.humidite = self.capteur_humidite_temp.humidity()
		self.temp = self.capteur_humidite_temp.temperature()

		self.capteur_co2_nano.getRawSensorValue()
		self.co2 = self.capteur_co2_nano.CO2eq()
		self.nano = self.capteur_co2_nano.TVoC()

		self.son = self.capteur_sensor_son.getRawSensorValue()
		print(self.son)
		self.mouvement = self.capteur_mouvement.getSensorValue()

		# récupère le status du boutton led (relaché ou non)
		self.bouton_relache = self.button_led_sensor.getStatusButton()

		#Ajout des valeurs dans les listes respectives pour agregation plus tard
		self.liste_horaire.append(self.horaire)
		self.liste_humidite.append(self.humidite)
		self.liste_temperature.append(self.temp)
		self.liste_co2.append(self.co2)
		self.liste_nano_particules.append(self.nano)
		self.liste_son.append(self.son)

	def inputProcessing(self):
		#print("Traitement des entrées")
		print("")
		self.date_jour = dt.datetime.now()
		#self.client.publish("test_channel", str(self.date_jour))

	def graph(self):
		#print("Graph d'état")
		# 2 modes : jour et nuit (uniquement le capteur de mouvement)

		if self.horaire_ouverture <= self.horaire <= self.horaire_fermeture :
			if self.etat == 14:
				self.etat = 2 # état mode autonome -> affichage des 5 valeurs de capteurs sur le led stick
			if self.etat == 0 :
				if self.bouton_relache == 0 : # le boutton est enfoncé
					self.etat = 1
					return self.etat
			if self.etat == 1 :
				if self.bouton_relache == 1 : # le boutton est relaché
					self.etat = 2 # état mode autonome
					return self.etat
			if self.etat == 2 :
				if self.bouton_relache == 0 :
					self.etat = 3
					return self.etat
			if self.etat == 3 :
				if self.bouton_relache == 1 :
					self.etat = 4 # mode manuel -> affichage dynamique des valeurs de température
					return self.etat
			if self.etat == 4 :
				if self.bouton_relache == 0 :
					self.etat = 5
					return self.etat
			if self.etat == 5 :
				if self.bouton_relache == 1 :
					self.etat = 6 # mode manuel -> affichage dynamique des valeurs d'humidité
					return self.etat
			if self.etat == 6 :
				if self.bouton_relache == 0 :
					self.etat = 7
					return self.etat
			if self.etat == 7 :
				if self.bouton_relache == 1 :
					self.etat = 8 # mode manuel -> affichage dynamique des valeurs de co2
					return self.etat
			if self.etat == 8 :
				if self.bouton_relache == 0 :
					self.etat = 9
					return self.etat
			if self.etat == 9 :
				if self.bouton_relache == 1 :
					self.etat = 10 # mode manuel -> affichage dynamique des valeurs de nano particules
					return self.etat
			if self.etat == 10 :
				if self.bouton_relache == 0 :
					self.etat = 11
					return self.etat
			if self.etat == 11 :
				if self.bouton_relache == 1 :
					self.etat = 12 # avant 0 # mode manuel -> affichage dynamique des valeurs de bruit
					return self.etat
			# rajoute mode autonome nano particules
			if self.etat == 12 :
				if self.bouton_relache == 0 :
					self.etat = 13
					return self.etat
			if self.etat == 13 :
				if self.bouton_relache == 1:
					self.etat = 0
					return self.etat
		else: # mode nuit (capteur de présence)
			self.etat = 14


	def outputProcessing(self):
		#print("Traitement des sorties")
		print("")
		# périodise la saisie des données dans le csv toutes les minutes
		# On insère une moyenne des valeurs des capteurs au cours des 60 dernières secondes

		# il faut au moins deux temporalités pour savoir si 60 secondes se sont écoulées
		self.horaire = dt.datetime.now().time()
		if len(self.liste_horaire) <= 1:
			self.ecriture_fichier = False
			return
		else:
			# si 60 secondes se sont écoulés entre la dernière saisie dans la liste et la première période saisie
			self.tmp_actuel = self.liste_horaire[-1]
			print(self.tmp_actuel)
			self.premier_temps = self.liste_horaire[0].hour * 3600 + self.liste_horaire[0].minute * 60 + self.liste_horaire[0].second
			print(self.premier_temps)
			self.seconds_debut = self.tmp_actuel.hour * 3600 + self.tmp_actuel.minute * 60 + self.tmp_actuel.second
			print(self.seconds_debut)
			if self.seconds_debut - self.premier_temps > 20:

				#on réalise un agrégat moyenne sur toutes les valeurs des capteurs
				self.avg_humidite = round(float(np.mean(self.liste_humidite)),2)
				self.avg_temperature = round(float(np.mean(self.liste_temperature)),2)
				self.avg_co2 = round(float(np.mean(self.liste_co2)),2)
				self.avg_nano = round(float(np.mean(self.liste_nano_particules)),2)
				self.avg_son = round(float(np.mean(self.liste_son)),2)

				# on a consommé les 60 secondes, on repart sur un nouveau cycle de calcul
				self.liste_horaire.clear()
				self.liste_humidite.clear()
				self.liste_temperature.clear()
				self.liste_co2.clear()
				self.liste_nano_particules.clear()
				self.liste_son.clear()
				self.ecriture_fichier = True
			else:
				self.ecriture_fichier = False
		self.client.publish("test_channel", f"\nhumidité : {self.humidite}\ntemperature : {self.temp}\nco2 : {self.co2}\nnano particules : {self.nano}\n son : {self.son} ")

	def outputUpdate(self):
		print(self.etat)

		self.i = 0 # réinitialise i pour nouveau tour de boucle
		if self.etat == 0:
			self.led_stick.LedRGB_AllOFF()
		if self.etat == 2 : # mode autonome

			# affichage d'un des 5 niveaux de températures sur la 1er LED du stick (indice 0)
			if self.temp < self.temp_seuil[0] :
				self.led_stick.LedRGB_ON(0,0,0,139) # très froid
				self.buzzer_temp = 1
			elif self.temp < self.temp_seuil[1] :
				self.led_stick.LedRGB_ON(0,173,216,230) # froid
				self.buzzer_temp = 0
			elif self.temp < self.temp_seuil[2] :
				self.led_stick.LedRGB_ON(0,0,128,0) # normale
				self.buzzer_temp = 0
			elif self.temp < self.temp_seuil[3] :
				self.led_stick.LedRGB_ON(0,255,128,0) # chaud
				self.buzzer_temp = 0
			else :
				self.led_stick.LedRGB_ON(0,255,0,0) # très chaud
				self.buzzer_temp = 1

			self.liste_buzzer_auto.append(self.buzzer_temp)

			# affichage d'un des 3 niveaux d'humidité sur la 3ème LED du stick (indice 2)
			if self.humidite < self.humidite_seuil[0]: # sec
				self.led_stick.LedRGB_ON(2,255,0,0)
				self.buzzer_hum = 1
			elif self.humidite >= self.humidite_seuil[0] and self.humidite < self.humidite_seuil[1]: # normal
				self.led_stick.LedRGB_ON(2,0,255,0)
				self.buzzer_hum = 0
			else :
				self.led_stick.LedRGB_ON(2,0,0,255) # humide
				self.buzzer_hum = 1

			self.liste_buzzer_auto.append(self.buzzer_hum)

			# affichage d'un des 5 niveaux de concentration de Co2 sur la 5ème LED du stick (indice 4)
			if self.co2 < self.co2_seuil[0] :
				self.led_stick.LedRGB_ON(4,0,128,0) # excellent
				self.buzzer_co2 = 0
			elif self.co2 < self.co2_seuil[1] :
				self.led_stick.LedRGB_ON(4,0,255,0) # bon
				self.buzzer_co2 = 0
			elif self.co2 < self.co2_seuil[2] :
				self.led_stick.LedRGB_ON(4,255,255,0) #ok
				self.buzzer_co2 = 0
			elif self.co2 < self.co2_seuil[3] :
				self.led_stick.LedRGB_ON(4,255,128,0) # mauvais
				self.buzzer_co2 = 1
			else :
				self.led_stick.LedRGB_ON(4,255,0,0) # très mauvais
				self.buzzer_co2 = 1

			self.liste_buzzer_auto.append(self.buzzer_co2)

			# affichage d'un des 5 niveaux de concentration de nano particules sur la 7ème LED du stick (indice 6)
			if self.nano < self.nano_seuil[0] :
				self.led_stick.LedRGB_ON(6,0,128,0) # très bon
				self.buzzer_nano = 0
			elif self.nano < self.nano_seuil[1] :
				self.led_stick.LedRGB_ON(6,0,255,0) # bon
				self.buzzer_nano = 0
			elif self.nano < self.nano_seuil[2] :
				self.led_stick.LedRGB_ON(6,255,255,0) # moyen
				self.buzzer_nano = 0
			elif self.nano < self.nano_seuil[3] :
				self.led_stick.LedRGB_ON(6,255,128,0) # élevé
				self.buzzer_nano = 1
			else :
				self.led_stick.LedRGB_ON(6,255,0,0) # très élevé
				self.buzzer_nano = 1

			self.liste_buzzer_auto.append(self.buzzer_nano)

			# affichage d'un des 5 niveaux de bruit sur la 9ème LED du stick (indice 8)
			if self.son < self.son_seuil[0] :
				self.led_stick.LedRGB_ON(8,0,128,0) # très calme
				self.buzzer_son = 0
			elif self.son < self.son_seuil[1] :
				self.led_stick.LedRGB_ON(8,0,255,0) # calme
				self.buzzer_son = 0
			elif self.son < self.son_seuil[2] :
				self.led_stick.LedRGB_ON(8,255,255,0) # agité
				self.buzzer_son = 0
			elif self.son < self.son_seuil[3] :
				self.led_stick.LedRGB_ON(8,255,128,0) # bruyant
				self.buzzer_son = 1
			else :
				self.led_stick.LedRGB_ON(8,255,0,0) #très bruyant
				self.buzzer_son = 1

			self.liste_buzzer_auto.append(self.buzzer_son)

			if 1 in self.liste_buzzer_auto:
				self.isBuzzer = 1
			else:
				self.isBuzzer = 0

		if self.etat == 4 : # mode manuel pour la température
			if self.temp < self.temp_seuil[0]:
				for self.j in range(2, 10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(2): # en reprenant les seuils precedemment abordés, affichage dynamique du nb de LED allumé + couleur
					self.led_stick.LedRGB_ON(self.i,0,0,139)
				self.isBuzzer = 1 # il fait très froid -> buzzer
			elif self.temp < self.temp_seuil[1]:
				self.j = 4
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(4):
					self.led_stick.LedRGB_ON(self.i,173,216,230)
				self.isBuzzer = 0
			elif self.temp < self.temp_seuil[2]:
				self.j = 6
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(6):
					self.led_stick.LedRGB_ON(self.i,0,128,0)
				self.isBuzzer = 0
			elif self.temp < self.temp_seuil[3]:
				self.j = 8
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(8):
					self.led_stick.LedRGB_ON(self.i,255,128,0)
				self.isBuzzer = 0
			else:
				for self.i in range(10):
					self.led_stick.LedRGB_ON(self.i,255,0,0)
				self.isBuzzer = 1 # il fait très chaud -> buzzer


		elif self.etat == 6 : # mode manuel pour humidité
			if self.humidite < self.humidite_seuil[0]:
				self.j = 3
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(3) : # affichage dynamique du nb de LED en fonction du niveau d'humidité
					self.led_stick.LedRGB_ON(self.i,255,0,0)
				self.isBuzzer = 1
			elif self.humidite < self.humidite_seuil[1]:
				self.j = 7
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(7) :
					self.led_stick.LedRGB_ON(self.i,0,255,0)
				self.isBuzzer = 0
			else:
				for self.i in range(10) :
					self.led_stick.LedRGB_ON(self.i,0,0,255)
				self.isBuzzer = 1


		elif self.etat == 8 : # mode manuel Co2
			print(self.co2)
			if self.co2 < self.co2_seuil[0]:
				for self.j in range(2, 10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(2):
					self.led_stick.LedRGB_ON(self.i,0,128,0)
				self.isBuzzer = 0
			elif self.co2 < self.co2_seuil[1]:
				for self.j in range(4, 10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(4):
					self.led_stick.LedRGB_ON(self.i,0,255,0)
				self.isBuzzer = 0
			elif self.co2 < self.co2_seuil[2]:
				self.j = 6
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(6):
					self.led_stick.LedRGB_ON(self.i,255,255,0)
				self.isBuzzer = 0
			elif  self.co2 < self.co2_seuil[3]:
				self.j = 8
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(8):
					self.led_stick.LedRGB_ON(self.i,255,128,0)
				self.isBuzzer = 1
			else:
				for self.i in range(10):
					self.led_stick.LedRGB_ON(self.i,255,0,0)
				self.isBuzzer = 1


		elif self.etat == 10 : # mode manuel nano particules
			if self.nano < self.nano_seuil[0] :
				self.j = 2
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(2):
					self.led_stick.LedRGB_ON(self.i,0,128,0)
				self.isBuzzer = 0
			elif self.nano < self.nano_seuil[1] :
				self.j = 4
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(4):
					self.led_stick.LedRGB_ON(self.i,0,255,0)
				self.isBuzzer = 0
			elif self.nano < self.nano_seuil[2] :
				self.j = 6
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(6):
					self.led_stick.LedRGB_ON(self.i,255,255,0)
				self.isBuzzer = 0
			elif self.nano < self.nano_seuil[3] :
				self.j = 8
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(8):
					self.led_stick.LedRGB_ON(self.i,255,128,0)
				self.isBuzzer = 1
			else :
				for self.i in range(10):
					self.led_stick.LedRGB_ON(self.i,255,0,0)
				self.isBuzzer = 1

		elif self.etat == 12 : # mode manuel bruit
			if self.son < self.son_seuil[0]:
				self.j = 2
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(2):
					self.led_stick.LedRGB_ON(self.i,0,128,0)
				self.isBuzzer = 0
			elif  self.son < self.son_seuil[1]:
				self.j = 4
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(4):
					self.led_stick.LedRGB_ON(self.i,0,255,0)
				self.isBuzzer = 0
			elif self.son < self.son_seuil[2]:
				self.j = 6
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(6):
					self.led_stick.LedRGB_ON(self.i,255,255,0)
				self.isBuzzer = 0
			elif self.son < self.son_seuil[3]:
				self.j = 8
				for self.j in range(10):
					self.led_stick.LedRGB_OFF(self.j)
				for self.i in range(8):
					self.led_stick.LedRGB_ON(self.i,255,128,0)
				self.isBuzzer = 1
			else:
				for self.i in range(10):
					self.led_stick.LedRGB_ON(self.i,255,0,0)
				self.isBuzzer = 1

		elif self.etat == 14: # mode spécial nuit où le capteur de présence domine les autres
			if self.mouvement == 1:
				self.led_stick.LedRGB_AllON(10, 255, 0, 0) # un individu est présent à une heure suspecte
				self.isBuzzer = 1 # allume buzzer

		# on éteint les LED quand elles sont dans un état intermediaire (entre deux capteurs)		
		elif self.etat in [1, 3, 5, 7, 9, 11, 13]:
			self.led_stick.LedRGB_AllOFF()
			self.isBuzzer = 0

		if self.isBuzzer==0:
				self.buzzer.off()
		elif self.isBuzzer==1:
			self.buzzer.on()

		# si 60 secondes se sont passés -> on écrit les agrégats dans le csv
		if self.ecriture_fichier == True:
			with open("all_data.csv", "a") as f:
					f.write(f'{self.date_jour.strftime("%d/%m/%Y")};{self.horaire.strftime("%H:%M:%S")};{self.avg_temperature};{self.avg_humidite};{self.avg_co2};{self.avg_nano};{self.avg_son}\n')

			# on réintialise les variables d'agregats à 0
			self.avg_humidite = 0
			self.avg_temperature = 0
			self.avg_co2 = 0
			self.avg_nano = 0
			self.avg_son = 0


"""
		self.liste_time.append(self.horaire.strftime("%H:%M:%S"))
		self.liste_humidite.append(self.humidite)
		self.liste_temperature.append(self.temp)
		self.liste_co2.append(self.co2)
		self.liste_nano_particules.append(self.nano)
		self.liste_son.append(self.son)

"""
def on_connect(client, userdata, flags, rc) :
	if rc == 0 :
		print("Connection success !")
	else :
		print("connection failure !")

	client.publish("test_channel", "test publish depuis python")

def on_publish(client, userdata, mid) :
	print("msg publié !")

