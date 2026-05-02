#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_NeoPixel.h>

const char* ssid     = "Desktop_F8A94029";
const char* password = "9895004130331967";

const char* serverUrl = "http://192.168.137.69:5000/update";

#define BOTAO_ENVIO   5
#define BOTAO_URGENTE 18
#define POT     34
#define LED_PIN  14

#define NUM_LEDS 10
#define GRUPO    2

Adafruit_NeoPixel fita(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// ─── CONTROLE ───────────────────────────
unsigned long lastDebounceEnvio = 0;
unsigned long lastDebounceUrgente = 0;
unsigned long debounceDelay = 50;

unsigned long lastSendTime = 0;
unsigned long sendCooldown = 3000;

bool lastEnvioState = HIGH;
bool lastUrgenteState = HIGH;

bool envioState;
bool urgente = false;

// ─── LED ────────────────────────────────
uint32_t corPorNivel(int nivel) {
  float t = (float)(nivel - 1) / (NUM_LEDS - 1);

  uint8_t r, g;

  if (t <= 0.5f) {
    r = t * 2 * 255;
    g = 255;
  } else {
    r = 255;
    g = (1 - (t - 0.5f) * 2) * 255;
  }

  return fita.Color(r, g, 0);
}

void atualizarFita(int nivel) {
  fita.clear();

  for (int i = 0; i < nivel; i++) {
    fita.setPixelColor(i, corPorNivel(nivel));
  }

  fita.show();
}

// ─── WIFI ───────────────────────────────
void garantirWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.disconnect();
  WiFi.begin(ssid, password);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 10) {
    delay(500);
    tentativas++;
  }
}

// ─── ENVIO HTTP ─────────────────────────
void enviarDados(int nivel) {
  garantirWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;

  String url = String(serverUrl) +
               "?grupo=" + GRUPO +
               "&nivel=" + nivel +
               "&urgente=" + String(urgente);

  for (int i = 0; i < 3; i++) {
    http.begin(url);
    int code = http.GET();

    if (code > 0) {
      http.end();
      return;
    }

    http.end();
    delay(500);
  }
}

// ─── SETUP ──────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(BOTAO_ENVIO, INPUT_PULLUP);
  pinMode(BOTAO_URGENTE, INPUT_PULLUP);
  pinMode(POT, INPUT);

  fita.begin();
  fita.setBrightness(80);
  fita.show();

  WiFi.begin(ssid, password);
}

// ─── LOOP ───────────────────────────────
void loop() {
  int valorPot = analogRead(POT);
  int nivel = map(valorPot, 0, 4095, 1, NUM_LEDS);

  atualizarFita(nivel);

  // ─── BOTÃO URGENTE (TOGGLE) ───
  int readUrgente = digitalRead(BOTAO_URGENTE);

  if (readUrgente != lastUrgenteState) {
    lastDebounceUrgente = millis();
  }

  if ((millis() - lastDebounceUrgente) > debounceDelay) {
    if (readUrgente == LOW && lastUrgenteState == HIGH) {
      urgente = !urgente;
    }
  }

  lastUrgenteState = readUrgente;

  // ─── BOTÃO ENVIO ───
  int readEnvio = digitalRead(BOTAO_ENVIO);

  if (readEnvio != lastEnvioState) {
    lastDebounceEnvio = millis();
  }

  if ((millis() - lastDebounceEnvio) > debounceDelay) {
    if (readEnvio == LOW && envioState == HIGH) {
      if (millis() - lastSendTime > sendCooldown) {
        enviarDados(nivel);
        lastSendTime = millis();
      }
    }
    envioState = readEnvio;
  }

  lastEnvioState = readEnvio;
}