import paho.mqtt.client as mqtt
import json
import time
import random

# Konfigurasi MQTT Broker lokal
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sensor"

print("=== SIMULATOR DATA ESP32 (BUDIDAYA MAGGOT BSF) ===")
print(f"Menghubungkan ke broker MQTT lokal di {MQTT_BROKER}:{MQTT_PORT}...")

try:
    if hasattr(mqtt, 'CallbackAPIVersion'):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    else:
        client = mqtt.Client()
        
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("✅ Simulator terhubung!")
    print(f"Mulai mengirimkan data sensor tiruan ke topik '{MQTT_TOPIC}' setiap 5 detik...")
    print("Tekan Ctrl+C untuk menghentikan simulator.\n")
    
    # Skenario pengujian (Suhu & Kelembaban bervariasi)
    scenarios = [
        # (Suhu, Kelembaban, Status Sistem)
        (29.5, 70.2, "NORMAL"),      # Optimal untuk Maggot
        (25.4, 65.5, "NORMAL"),      # Cukup Baik
        (34.2, 55.1, "NORMAL"),      # Cukup Baik
        (21.0, 48.5, "PERINGATAN"),  # Kurang Optimal
        (38.5, 92.4, "PERINGATAN"),  # Kurang Optimal
        (12.2, 35.0, "BAHAYA"),      # Berisiko
        (42.5, 97.0, "BAHAYA"),      # Berisiko
    ]
    
    scenario_idx = 0
    while True:
        # Mengambil skenario secara bergantian dengan sedikit variasi acak
        base_temp, base_hum, status = scenarios[scenario_idx]
        temp = round(base_temp + random.uniform(-0.5, 0.5), 1)
        hum = round(base_hum + random.uniform(-1.0, 1.0), 1)
        
        # Kemas dalam JSON payload
        payload = {
            "temp": temp,
            "hum": hum,
            "status": status
        }
        
        # Kirim data
        client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"📡 [KIRIM] Suhu: {temp} °C | Kelembaban: {hum} % | Status: {status}")
        
        scenario_idx = (scenario_idx + 1) % len(scenarios)
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\n🛑 Simulator dihentikan.")
except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
