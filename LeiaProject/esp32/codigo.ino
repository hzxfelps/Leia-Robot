#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_NeoPixel.h>

// ─── CONFIG ─────────────────────────────────────
const char* ssid     = "Desktop_F8A94029"; // REDE
const char* password = "9895004130331967"; // SENHA
const char* serverUrl = "http://192.168.1.11:5000/update"; //SEU IP

#define BOTAO   5
#define POT     34
#define LED_PIN 6

#define NUM_LEDS 10
#define GRUPO 1

Adafruit_NeoPixel fita(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// ─── CONTROLE ───────────────────────────────────
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

unsigned long lastSendTime = 0;
unsigned long sendCooldown = 3000; // 3s entre envios

bool lastButtonState = HIGH;
bool buttonState;

// ─── CORES ─────────────────────────────────────
uint32_t corPorNivel(int nivel) {
  float t = (float)(nivel - 1) / (NUM_LEDS - 1);

  uint8_t r, g;

  if (t <= 0.5f) {
    r = t * 2.0f * 255;
    g = 255;
  } else {
    r = 255;
    g = (1.0f - (t - 0.5f) * 2.0f) * 255;
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

// ─── WIFI ──────────────────────────────────────
void garantirWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println("Reconectando WiFi...");
  WiFi.disconnect();
  WiFi.begin(ssid, password);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 10) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi reconectado!");
  } else {
    Serial.println("\nFalha ao reconectar WiFi");
  }
}

// ─── HTTP COM RETRY ────────────────────────────
void enviarDados(int nivel) {
  garantirWiFi();

  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(serverUrl) + "?grupo=" + GRUPO + "&nivel=" + nivel + "&urgente=1";

  for (int i = 0; i < 3; i++) {
    http.begin(url);
    int code = http.GET();

    if (code > 0) {
      Serial.print("HTTP OK: ");
      Serial.println(code);
      http.end();
      return;
    }

    Serial.println("Erro HTTP, tentando novamente...");
    http.end();
    delay(500);
  }

  Serial.println("Falha após 3 tentativas.");
}

// ─── SETUP ─────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(BOTAO, INPUT_PULLUP);
  pinMode(POT, INPUT);

  fita.begin();
  fita.setBrightness(80);
  fita.show();

  WiFi.begin(ssid, password);

  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado!");
}

// ─── LOOP ──────────────────────────────────────
void loop() {
  // leitura contínua do nível
  int valorPot = analogRead(POT);
  int nivel = map(valorPot, 0, 4095, 1, NUM_LEDS);
  atualizarFita(nivel);

  // leitura botão com debounce
  int reading = digitalRead(BOTAO);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;

      if (buttonState == LOW) {
        if (millis() - lastSendTime > sendCooldown) {
          Serial.println("ENVIANDO...");
          enviarDados(nivel);
          lastSendTime = millis();
        } else {
          Serial.println("Cooldown ativo...");
        }
      }
    }
  }

  lastButtonState = reading;
}