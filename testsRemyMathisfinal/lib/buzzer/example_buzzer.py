import time
import buzzer

BuzzerAlert = buzzer.GroveBuzzer(22)
BuzzerAlert.on()
time.sleep(0.1)
BuzzerAlert.off()
