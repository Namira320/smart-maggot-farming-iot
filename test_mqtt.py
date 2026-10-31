import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Terhubung ke Server HiveMQ!")
        client.subscribe("iot/sensor")
        print("📡 Menunggu aliran data dari ESP32...")
    else:
        print(f"❌ Gagal terhubung, kode error: {rc}")

def on_message(client, userdata, msg):
    print(f"🔥 DATA MASUK DARI ESP32: {msg.payload.decode('utf-8')}")

print("Menghidupkan Radar Penangkap Data...")
try:
    if hasattr(mqtt, 'CallbackAPIVersion'):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, transport="websockets")
    else:
        client = mqtt.Client(transport="websockets")
        
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("broker.hivemq.com", 8000, 60)
    client.loop_forever()
except Exception as e:
    print("Error:", e)
