#import time
#from datetime import datetime
import gateway3

print("Initialisation de l'application")
passerelleObject = gateway3.gateway()
print("Lancement de l'application")

# Durée de collecte (en secondes)
#duration = 5 * 60  # 5 minutes
#start_time = time.time()

while True:
	#print("salut-")
	passerelleObject.inputUpdate()
	passerelleObject.inputProcessing()
	passerelleObject.graph()
	passerelleObject.outputProcessing()
	passerelleObject.outputUpdate()

"""
	time.sleep(0.1)

	if time.time() - start_time == 0: # condition à modifier

		df = pd.DataFrame({
			"timestamp": passerelleObject.liste_time,
			"humidité": passerelleObject.humidite,
			"temperature": passerelleObject.temp,
			"CO2": passerelleObject.co2,
			"Nano particules": passerelleObject.nano,
			"niveau sonore": passerelleObject.son,
			"mouvement": passerelleObject.mouvement
		})

		# Exportation en CSV
		output_file = "C:/3eme_annee/Rawsberry_Pi/testsRemyMathisv2/capteurs_data.csv"
		df.to_csv(output_file, index=False)
		print(f"Les données ont été enregistrées dans le fichier : {output_file}")

		time.sleep(1)
"""
