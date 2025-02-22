import paho.mqtt as mqtt


def on_connect(client, userdata, rs):
	if rs == 0:
		print("Connexion succefull")
	else:
		print("Connexion failure")

	client.publish("test_channel", "premier msg")

def on_publish(client, userdata, xx):
	print("msg_envoye")


client = mqtt.Client()
