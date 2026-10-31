#include <Wire.h>

void setup() {
  Wire.begin(21, 22);
  Serial.begin(115200);
  while (!Serial);
  Serial.println("\nI2C Scanner");
}

void loop() {
  byte error, address;
  int nDevices;
  Serial.println("Scanning...");
  nDevices = 0;
  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("Alamat I2C LCD kamu ditemukan di: 0x");
      if (address<16) {
        Serial.print("0");
      }
      Serial.println(address,HEX);
      nDevices++;
    }
  }
  if (nDevices == 0) {
    Serial.println("LCD Tidak Terdeteksi! (Cek kabel VCC, GND, SDA, SCL)");
  } else {
    Serial.println("Selesai.\n");
  }
  delay(5000);
}
