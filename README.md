# 🐛 Smart Maggot Farming IoT

An Internet of Things (IoT) project for real-time environmental monitoring using an **ESP32** microcontroller, **DHT22** sensor, **MQTT protocol**, and a **Python Streamlit** web dashboard. 

---

## 📺 Demo Video
[![Watch the video](https://img.youtube.com/vi/fSSndOG5Fng/hqdefault.jpg)](https://youtu.be/fSSndOG5Fng)

## 📄 Project Documentation

[smart-maggot-farming-iot](./smart-maggot-farming-iot.pdf)

---

## 🔍 Overview

Environmental parameters such as temperature and relative humidity require strict monitoring across agricultural and cultivation sectors (such as 🐛 maggot farming) to ensure optimal growth conditions. 

This project implements an end-to-end IoT monitoring pipeline:
1. **Physical Layer:** The ESP32 collects telemetry data via a DHT22 sensor and drives local audiovisual alerts (Tri-LEDs and an active buzzer) alongside an I2C 16x2 LCD.
2. **Network Layer:** Data is published in JSON format over a lightweight MQTT protocol using a local Eclipse Mosquitto broker.
3. **Application Layer:** A real-time, interactive **Streamlit** web dashboard displays live metrics, historical data logs, and visual trend charts.

---

## 🏗️ System Architecture

The system follows a modular 3-tier architecture:

```text
[ Hardware Node (ESP32 + DHT22) ] 
       │ (Publish JSON via Wi-Fi)
       ▼
[ Local MQTT Broker (Eclipse Mosquitto - Intranet IP) ] 
       │ (Subscribe / Stream Data)
       ▼
[ Streamlit Web Dashboard (Python Application) ]

```

---

## ✨ Key Features

* **Real-Time Sensor Acquisition:** High-precision temperature and humidity readings every 5 seconds using the DHT22 sensor to maintain ideal 🐛 maggot growth environments.
* **Autonomous Triage Logic:** Firmware-level state machine categorizing environment conditions into **NORMAL**, **WARNING (PERINGATAN)**, and **DANGER (BAHAYA)**.
* **Local Audiovisual Feedback:** Integrated 16x2 I2C LCD (at address `0x27`), Tri-LED indicators, and an active buzzer alarm.
* **Low-Latency MQTT Communication:** Utilizes a local Eclipse Mosquitto broker achieving sub-15ms latency with zero packet loss.
* **Interactive Web Dashboard:** Built with Streamlit, featuring instant metrics, dynamic status banners, a reverse-chronological log table (capped at 30 rows), and live line charts.
* **Synchronous Polling Mechanism:** Overcomes Streamlit's threading conflicts with `paho-mqtt` using a deterministic `client.loop()` and `st.session_state` persistence.

---

## 🛠️ Hardware Requirements & Pin Mapping

| Component | Component Pin | ESP32 GPIO Pin | Wire Color | Description / Function |
| --- | --- | --- | --- | --- |
| **DHT22 Sensor** | VCC | 3.3V | Red | Sensor power supply (3.3V DC) |
|  | DATA | GPIO 4 (D4) | Blue | Single-wire digital data line |
|  | GND | GND | Black | Shared grounding |
| **LCD 16x2 I2C** | VCC | Vin (5V) | Red | LCD power supply (5V DC for optimal brightness) |
|  | GND | GND | Black | Shared grounding |
|  | SDA | GPIO 21 | Yellow | I2C serial data line |
|  | SCL | GPIO 22 | White | I2C serial clock line |
| **Green LED 1** | Anode (+) | GPIO 33 (D33) | Purple | **NORMAL** condition indicator |
| **Green/Yellow LED 2** | Anode (+) | GPIO 27 (D27) | Green | **WARNING** condition indicator |
| **Red LED** | Anode (+) | GPIO 26 (D26) | Gray/Black | **DANGER** condition indicator |
| **Active Buzzer (5V)** | Positive (+) | GPIO 32 (D32) | Black | Audio alarm (driven directly by 3.3V GPIO output) |

---

## 🧠 Triage Logic & State Machine

The system determines environmental health based on pre-defined ideal thresholds:
- **Ideal Temperature (T):** 25.0°C ≤ T ≤ 35.0°C
- **Ideal Humidity (H):** 60.0% ≤ H ≤ 80.0%

1. **NORMAL:** Both T and H are within ideal ranges. *(Green LED 1 ON; others OFF; Buzzer OFF.)*
2. **WARNING (PERINGATAN):** Exactly one parameter is out of bounds. *(Green/Yellow LED ON; Buzzer ON continuously.)*
3. **DANGER (BAHAYA):** Both T and H simultaneously violate ideal ranges. *(Red LED ON; Buzzer ringing continuously.)*

---

## 📡 MQTT Payload Structure

Data packets are serialized into lightweight JSON objects to optimize bandwidth:

```json
{
  "temp": 28.5,
  "hum": 65.2,
  "status": "NORMAL"
}

```

*(Handled efficiently on the ESP32 using `ArduinoJson` with a static memory allocation of 128 bytes).*

---

## 🚀 Installation & Setup

### 1. Prerequisites

* Arduino IDE (with ESP32 board package installed)
* Python 3.8+ installed on your PC/Server
* Eclipse Mosquitto MQTT Broker installed locally

### 2. Hardware Assembly

* Wire the circuit components according to the Pin Mapping table using a breadboard.
* Ensure proper pull-up resistors are used for the DHT22 data line if necessary.

### 3. Firmware Setup (ESP32)
1. Open the Arduino IDE and load the sketch inside `kode IoT/maggot_iot_esp32/maggot_iot_esp32.ino`.
2. Install required libraries via Library Manager:
    - `DHT sensor library` by Adafruit
    - `LiquidCrystal_I2C`
    - `ArduinoJson` (v6.x)
    - `PubSubClient`
3. Update your Wi-Fi credentials and local MQTT broker IP address in the firmware code.
4. Compile and upload the code to your ESP32 board.

### 4. Dashboard Setup (Python)

1. Navigate to the project directory containing the Streamlit app.
2. Install dependencies:
```bash
pip install streamlit paho-mqtt pandas matplotlib

```


3. Run the Streamlit dashboard:
```bash
streamlit run dashboard.py

```



---

## 💡 Usage

1. Start your local Eclipse Mosquitto broker service:
```bash
mosquitto -v

```


2. Power on the ESP32 hardware node. Verify via the Serial Monitor and LCD screen that it connects to Wi-Fi and publishes data successfully.
3. Open the Streamlit web interface in your browser to view live telemetry metrics, status cards, historical logs, and real-time graphs.

---

## 📊 Troubleshooting & Optimizations

* **Public vs. Local MQTT Brokers:** Public cloud brokers introduce high latency and disconnection vulnerabilities. Switching to a **local Eclipse Mosquitto broker** reduced transmission latency significantly with zero packet loss.
* **Streamlit Threading Conflict:** Asynchronous background threads cause variable isolation and UI freezing in Streamlit. This project implements a **Synchronous Polling** mechanism using `client.loop(timeout=0.1)` combined with `st.session_state` and `st.rerun()` to ensure continuous, flicker-free data logging.

---

## 🔮 Future Improvements

* **Closed-Loop Actuation:** Integrate DC exhaust fans or humidifiers via relay modules to automatically correct environmental anomalies when a DANGER status is triggered to protect the 🐛 maggot cultivation zone.
* **Persistent Database Storage:** Replace temporary `st.session_state` memory with **SQLite** or **InfluxDB** for long-term historical data logging.
* **Extended Notifications:** Add IoT-based messaging alerts for remote warnings.

---

**Key Libraries & Standards:**

* *ArduinoJson* (B. Blanchon)
* *ESP32 Datasheet* (Espressif Systems)
* *DHT22 / AM2302 Sensor Specs* (Aosong Electronics)
* *Mosquitto MQTT* (R. A. Light)
* *PCF8574 I/O Expander* (NXP Semiconductors)
* *Streamlit Documentation*
