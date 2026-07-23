/*
 * Smart Irrigation & Climate Automation System
 * ----------------------------------------------
 * Platform: ESP32 DevKit
 *
 * Reads soil moisture, temperature/humidity, and ambient light, then
 * automates a water pump and a ventilation fan with hysteresis control
 * (to avoid relay chatter at the threshold boundary). Exposes a small
 * built-in web dashboard over WiFi for live status + manual override.
 *
 * Sensors:
 *   - DHT22            -> GPIO4   (temperature / humidity)
 *   - Soil moisture     -> GPIO34  (analog, capacitive sensor)
 *   - LDR light sensor   -> GPIO35  (analog, voltage divider)
 * Actuators:
 *   - Pump relay        -> GPIO26
 *   - Fan relay         -> GPIO27
 *
 * Author: polik (EE student)
 */

#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

// ---------------------------------------------------------------------------
// Pin configuration
// ---------------------------------------------------------------------------
#define DHTPIN        4
#define DHTTYPE       DHT22
#define SOIL_PIN      34
#define LDR_PIN       35
#define PUMP_RELAY    26
#define FAN_RELAY     27

// ---------------------------------------------------------------------------
// WiFi credentials - fill these in before flashing
// ---------------------------------------------------------------------------
const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASS = "YOUR_WIFI_PASSWORD";

// ---------------------------------------------------------------------------
// Automation thresholds (with hysteresis to prevent relay chatter)
// ---------------------------------------------------------------------------
const int SOIL_DRY_THRESHOLD  = 30;   // % below this -> start watering
const int SOIL_WET_THRESHOLD  = 55;   // % above this -> stop watering
const float TEMP_HOT_THRESHOLD = 29.0; // C above this -> fan on
const float TEMP_OK_THRESHOLD  = 26.0; // C below this -> fan off

// Safety: never run the pump longer than this in one cycle (dry-run / burst-pipe protection)
const unsigned long MAX_PUMP_RUNTIME_MS = 30UL * 1000UL; // 30 s

DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

bool pumpOn = false;
bool fanOn = false;
unsigned long pumpStartTime = 0;
bool manualOverride = false; // set true via dashboard to pause automation

float lastTemp = NAN, lastHumidity = NAN;
int lastSoilPct = -1, lastLightPct = -1;

// ---------------------------------------------------------------------------
// Sensor reading helpers
// ---------------------------------------------------------------------------
int readSoilPercent() {
  int raw = analogRead(SOIL_PIN);           // 0-4095 on ESP32 ADC
  // Calibrate for your sensor: raw ~ 2800 in dry air, ~1200 fully submerged.
  int pct = map(raw, 2800, 1200, 0, 100);
  return constrain(pct, 0, 100);
}

int readLightPercent() {
  int raw = analogRead(LDR_PIN);
  return constrain(map(raw, 0, 4095, 0, 100), 0, 100);
}

// ---------------------------------------------------------------------------
// Automation logic - hysteresis control so relays don't chatter at the edge
// ---------------------------------------------------------------------------
void runAutomation() {
  if (manualOverride) return;

  // --- Irrigation control ---
  if (!pumpOn && lastSoilPct >= 0 && lastSoilPct < SOIL_DRY_THRESHOLD) {
    pumpOn = true;
    pumpStartTime = millis();
    digitalWrite(PUMP_RELAY, HIGH);
    Serial.println("[AUTOMATION] Soil dry -> pump ON");
  } else if (pumpOn && lastSoilPct >= SOIL_WET_THRESHOLD) {
    pumpOn = false;
    digitalWrite(PUMP_RELAY, LOW);
    Serial.println("[AUTOMATION] Soil wet -> pump OFF");
  }

  // Safety cutoff regardless of sensor reading
  if (pumpOn && (millis() - pumpStartTime > MAX_PUMP_RUNTIME_MS)) {
    pumpOn = false;
    digitalWrite(PUMP_RELAY, LOW);
    Serial.println("[SAFETY] Max pump runtime exceeded -> pump forced OFF");
  }

  // --- Climate control ---
  if (!isnan(lastTemp)) {
    if (!fanOn && lastTemp > TEMP_HOT_THRESHOLD) {
      fanOn = true;
      digitalWrite(FAN_RELAY, HIGH);
      Serial.println("[AUTOMATION] Too hot -> fan ON");
    } else if (fanOn && lastTemp < TEMP_OK_THRESHOLD) {
      fanOn = false;
      digitalWrite(FAN_RELAY, LOW);
      Serial.println("[AUTOMATION] Cooled down -> fan OFF");
    }
  }
}

// ---------------------------------------------------------------------------
// Web dashboard
// ---------------------------------------------------------------------------
void handleRoot() {
  String html = "<html><head><meta http-equiv='refresh' content='5'>";
  html += "<title>Automation Dashboard</title></head><body style='font-family:sans-serif'>";
  html += "<h2>Smart Irrigation & Climate Automation</h2>";
  html += "<p>Temperature: " + String(lastTemp) + " C</p>";
  html += "<p>Humidity: " + String(lastHumidity) + " %</p>";
  html += "<p>Soil moisture: " + String(lastSoilPct) + " %</p>";
  html += "<p>Light level: " + String(lastLightPct) + " %</p>";
  html += "<p>Pump: " + String(pumpOn ? "ON" : "OFF") + "</p>";
  html += "<p>Fan: " + String(fanOn ? "ON" : "OFF") + "</p>";
  html += "<p>Manual override: " + String(manualOverride ? "ENABLED" : "disabled") + "</p>";
  html += "<p><a href='/toggle-override'>Toggle manual override</a></p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleToggleOverride() {
  manualOverride = !manualOverride;
  server.sendHeader("Location", "/");
  server.send(303);
}

// ---------------------------------------------------------------------------
// Setup / loop
// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(PUMP_RELAY, OUTPUT);
  pinMode(FAN_RELAY, OUTPUT);
  digitalWrite(PUMP_RELAY, LOW);
  digitalWrite(FAN_RELAY, LOW);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. Dashboard at: http://");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/toggle-override", handleToggleOverride);
  server.begin();
}

unsigned long lastSensorRead = 0;
const unsigned long SENSOR_INTERVAL_MS = 2000;

void loop() {
  server.handleClient();

  if (millis() - lastSensorRead >= SENSOR_INTERVAL_MS) {
    lastSensorRead = millis();
    lastTemp = dht.readTemperature();
    lastHumidity = dht.readHumidity();
    lastSoilPct = readSoilPercent();
    lastLightPct = readLightPercent();

    Serial.printf("Temp=%.1fC  Hum=%.1f%%  Soil=%d%%  Light=%d%%\n",
                  lastTemp, lastHumidity, lastSoilPct, lastLightPct);

    runAutomation();
  }
}
