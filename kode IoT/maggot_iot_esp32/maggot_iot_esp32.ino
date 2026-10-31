/*
 * ============================================================
 *  SISTEM MONITORING BUDIDAYA MAGGOT BSF - IoT ESP32
 *  Proyek: Digitalisasi Budidaya Maggot Sekolah
 * ============================================================
 *  Hardware:
 *    - ESP32
 *    - DHT22     → Pin D4
 *    - LCD I2C   → SDA=D21, SCL=D22
 *    - LED Hijau → D5  (kondisi NORMAL)
 *    - LED Hijau → D18 (kondisi NORMAL 2)
 *    - LED Merah → D15 (kondisi PERINGATAN)
 *    - Buzzer    → D12
 *
 *  Protokol: MQTT → Broker localhost:1883
 *  Topic publish : iot/sensor
 *  Format JSON   : {"temp": 28.5, "hum": 65.2, "status": "NORMAL"}
 * ============================================================
 *
 *  Library yang dibutuhkan (install via Arduino Library Manager):
 *    1. DHT sensor library  (Adafruit)
 *    2. Adafruit Unified Sensor
 *    3. PubSubClient        (Nick O'Leary)
 *    4. LiquidCrystal_I2C   (Frank de Brabander)
 *    5. ArduinoJson         (Benoit Blanchon)
 * ============================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────
//  KONFIGURASI — SESUAIKAN DI SINI
// ─────────────────────────────────────────────

// WiFi
const char* WIFI_SSID     = "ㅎㅎㅎㅎㅎ";
const char* WIFI_PASSWORD = "part12345";

// MQTT Broker (IP komputer yang menjalankan Mosquitto)
// Ganti dengan IP lokal komputer kamu, contoh: "192.168.1.10"
// Cara cek IP komputer: buka CMD → ketik "ipconfig" (Windows)
const char* MQTT_BROKER   = "172.25.154.119";
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "iot/sensor";
const char* CLIENT_ID     = "ESP32_Maggot_BSF";

// Interval kirim data (millisecond) — default 5 detik
const long  INTERVAL_MS   = 5000;

// ─────────────────────────────────────────────
//  BATAS SUHU & KELEMBABAN MAGGOT BSF
//  Referensi: suhu optimal BSF = 25–35°C, kelembaban = 60–80%
// ─────────────────────────────────────────────
const float SUHU_MIN  = 25.0;
const float SUHU_MAX  = 35.0;
const float HUM_MIN   = 60.0;
const float HUM_MAX   = 80.0;

// ─────────────────────────────────────────────
//  PIN DEFINITIONS (DisEsuaikan dengan Excel)
// ─────────────────────────────────────────────
#define DHT_PIN       4    // D4 (Kabel Coklat HARUS dicolok ke sini!)
#define DHT_TYPE      DHT22
#define LED_HIJAU_1   13   // D13 (Kabel Ungu)
#define LED_HIJAU_2   12   // D12 (Kabel Hijau)
#define LED_MERAH     14   // D14 (Kabel Hitam)
#define BUZZER_PIN    12   // D12 (Buzzer numpang di jalur LED Hijau 2)

// LCD I2C — alamat default 0x27 (cek dengan I2C Scanner jika beda)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ─────────────────────────────────────────────
//  OBJEK GLOBAL
// ─────────────────────────────────────────────
DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient   espClient;
PubSubClient mqttClient(espClient);

unsigned long lastSendTime = 0;

// ─────────────────────────────────────────────
//  SETUP
// ─────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Sistem Monitoring Maggot BSF ===");

  // Inisialisasi pin
  pinMode(LED_HIJAU_1, OUTPUT);
  pinMode(LED_HIJAU_2, OUTPUT);
  pinMode(LED_MERAH,   OUTPUT);
  pinMode(BUZZER_PIN,  OUTPUT);

  // Matikan semua indikator dulu
  digitalWrite(LED_HIJAU_1, LOW);
  digitalWrite(LED_HIJAU_2, LOW);
  digitalWrite(LED_MERAH,   LOW);
  digitalWrite(BUZZER_PIN,  LOW);

  // LCD
  Wire.begin(21, 22); // SDA=21, SCL=22
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Maggot BSF IoT");
  lcd.setCursor(0, 1);
  lcd.print("Menghubungkan...");

  // DHT22
  dht.begin();

  // WiFi
  connectWiFi();

  // MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  connectMQTT();

  // Tampilkan IP di Serial Monitor
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());
}

// ─────────────────────────────────────────────
//  LOOP UTAMA
// ─────────────────────────────────────────────
void loop() {
  // Jaga koneksi MQTT tetap aktif
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastSendTime >= INTERVAL_MS) {
    lastSendTime = now;
    bacaDanKirimData();
  }
}

// ─────────────────────────────────────────────
//  FUNGSI: Baca sensor & kirim ke MQTT
// ─────────────────────────────────────────────
void bacaDanKirimData() {
  float suhu = dht.readTemperature();
  float hum  = dht.readHumidity();

  // Cek apakah pembacaan valid
  if (isnan(suhu) || isnan(hum)) {
    Serial.println("[ERROR] Gagal membaca DHT22!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("ERROR: DHT22");
    lcd.setCursor(0, 1);
    lcd.print("Cek kabel!");
    return;
  }

  // Tentukan status kondisi
  String status = tentukanStatus(suhu, hum);

  // Tampilkan di LCD
  tampilkanLCD(suhu, hum, status);

  // Aktifkan indikator LED & buzzer
  aktifkanIndikator(status);

  // Kirim ke MQTT dalam format JSON
  kirimMQTT(suhu, hum, status);

  // Serial Monitor untuk debug
  Serial.printf("[DATA] Suhu: %.1f°C | Kelembaban: %.1f%% | Status: %s\n",
                suhu, hum, status.c_str());
}

// ─────────────────────────────────────────────
//  FUNGSI: Tentukan status kondisi maggot
// ─────────────────────────────────────────────
String tentukanStatus(float suhu, float hum) {
  bool suhuOk = (suhu >= SUHU_MIN && suhu <= SUHU_MAX);
  bool humOk  = (hum  >= HUM_MIN  && hum  <= HUM_MAX);

  if (suhuOk && humOk) {
    return "NORMAL";
  } else if (!suhuOk && !humOk) {
    return "BAHAYA";
  } else {
    return "PERINGATAN";
  }
}

// ─────────────────────────────────────────────
//  FUNGSI: Tampilkan ke LCD 16x2
// ─────────────────────────────────────────────
void tampilkanLCD(float suhu, float hum, String status) {
  lcd.clear();
  // Baris 1: Suhu & Kelembaban
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(suhu, 1);
  lcd.print("C H:");
  lcd.print(hum, 1);
  lcd.print("%");
  // Baris 2: Status
  lcd.setCursor(0, 1);
  lcd.print("Status: ");
  lcd.print(status);
}

// ─────────────────────────────────────────────
//  FUNGSI: Aktifkan LED & buzzer sesuai status
// ─────────────────────────────────────────────
void aktifkanIndikator(String status) {
  if (status == "NORMAL") {
    // LED hijau nyala, merah & buzzer mati
    digitalWrite(LED_HIJAU_1, HIGH);
    digitalWrite(LED_HIJAU_2, HIGH);
    digitalWrite(LED_MERAH,   LOW);
    noTone(BUZZER_PIN);
  } else if (status == "PERINGATAN") {
    // LED merah nyala, hijau mati, buzzer berbunyi pelan
    digitalWrite(LED_HIJAU_1, LOW);
    digitalWrite(LED_HIJAU_2, LOW);
    digitalWrite(LED_MERAH,   HIGH);
    tone(BUZZER_PIN, 1000, 200); // 1000Hz selama 200ms
  } else { // BAHAYA
    // Semua LED nyala bergantian, buzzer nyaring
    digitalWrite(LED_HIJAU_1, HIGH);
    digitalWrite(LED_MERAH,   HIGH);
    tone(BUZZER_PIN, 2000, 500); // 2000Hz selama 500ms
    delay(300);
    digitalWrite(LED_HIJAU_1, LOW);
    digitalWrite(LED_MERAH,   LOW);
  }
}

// ─────────────────────────────────────────────
//  FUNGSI: Kirim payload JSON ke MQTT
//  Format: {"temp":28.5,"hum":65.2,"status":"NORMAL"}
//  Sesuai dengan simulator_esp32.py kamu
// ─────────────────────────────────────────────
void kirimMQTT(float suhu, float hum, String status) {
  StaticJsonDocument<128> doc;
  doc["temp"]   = round(suhu * 10) / 10.0;
  doc["hum"]    = round(hum  * 10) / 10.0;
  doc["status"] = status;

  char payload[128];
  serializeJson(doc, payload);

  if (mqttClient.publish(MQTT_TOPIC, payload)) {
    Serial.printf("[MQTT] Terkirim → %s : %s\n", MQTT_TOPIC, payload);
  } else {
    Serial.println("[MQTT] GAGAL kirim, cek koneksi broker!");
  }
}

// ─────────────────────────────────────────────
//  FUNGSI: Koneksi WiFi
// ─────────────────────────────────────────────
void connectWiFi() {
  Serial.printf("Menghubungkan ke WiFi: %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Terhubung!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Terhubung!");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
    delay(1500);
  } else {
    Serial.println("\n[WiFi] GAGAL terhubung! Cek SSID/password.");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi GAGAL!");
    // ESP tetap jalan, akan retry otomatis
  }
}

// ─────────────────────────────────────────────
//  FUNGSI: Koneksi MQTT Broker
// ─────────────────────────────────────────────
void connectMQTT() {
  int retries = 0;
  while (!mqttClient.connected() && retries < 5) {
    Serial.printf("[MQTT] Menghubungkan ke %s:%d ...", MQTT_BROKER, MQTT_PORT);
    if (mqttClient.connect(CLIENT_ID)) {
      Serial.println(" Terhubung!");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("MQTT Terhubung!");
      delay(1000);
    } else {
      Serial.printf(" Gagal, rc=%d. Coba lagi...\n", mqttClient.state());
      retries++;
      delay(2000);
    }
  }
}
