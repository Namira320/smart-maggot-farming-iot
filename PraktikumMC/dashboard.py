import datetime
import json
import os
import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st
import time

st.title("Sistem Monitoring Maggot BSF")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temp": payload.get("temp"),
            "hum": payload.get("hum")
        }
        df = pd.DataFrame([record])
        if not os.path.isfile("data_sensor.csv"):
            df.to_csv("data_sensor.csv", index=False)
        else:
            df.to_csv("data_sensor.csv", mode='a', header=False, index=False)
    except Exception:
        pass

if "client" not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.subscribe("iot/sensor")
    client.loop_start()
    st.session_state.client = client

if os.path.exists("data_sensor.csv"):
    try:
        df = pd.read_csv("data_sensor.csv")
        if not df.empty:
            latest = df.iloc[-1]
            col1, col2 = st.columns(2)
            col1.metric("Suhu", f"{latest['temp']} °C")
            col2.metric("Kelembaban", f"{latest['hum']} %")
            
            # Buat grafik
            chart_data = df.set_index("timestamp")[["temp", "hum"]]
            st.line_chart(chart_data)
        else:
            st.write("Menunggu data sensor...")
    except Exception:
        st.write("Membaca data...")
else:
    st.write("Menunggu data sensor pertama...")

# Refresh halaman otomatis setiap 3 detik agar grafik bergerak
time.sleep(3)
st.rerun()
