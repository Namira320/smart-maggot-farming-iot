import json
import random
import time
import paho.mqtt.client as mqtt
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883, 60)
client.loop_start()
while True:
    suhu = round(random.uniform(25.0, 35.0), 1)
    kelembaban = round(random.uniform(55.0, 80.0), 1)
    payload = json.dumps({"temp": suhu, "hum": kelembaban})
    client.publish("iot/sensor", payload)
    time.sleep(3)
