#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <string>
#include <sstream>

#define LED_GREEN 16
#define LED_ONBOARD 2 
#define LED_RED 14

HTTPClient http;

// Stores the amount of ambient light to be able to turn off the LEDs
int ambientLight;

void setup() {
  // put your setup code here, to run once:
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_ONBOARD, OUTPUT);
  Serial.begin(9600);

  WiFi.begin("LYM-41626", "i5Ucawebi5Ucaweb");

  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());
  digitalWrite(LED_ONBOARD, LOW);
}

void loop() {
  digitalWrite(LED_GREEN, LOW);
  delay(1000);         
  digitalWrite(LED_GREEN, HIGH);
  delay(5000);       
  ambientLight = analogRead(A0);
  Serial.printf("Ambient Light: %d\n", ambientLight);

  char url[256];
  // sprintf(url, "http://192.168.1.136:5000/light?level=%d", ambientLight);
  sprintf(url, "http://onyx-outpost-122619.appspot.com/light?level=%d", ambientLight);
  http.begin(url);
  int httpCode = http.GET();  
  if (httpCode != 200) {
    digitalWrite(LED_RED, HIGH);
  } else {
    digitalWrite(LED_RED, LOW);
  }
  http.end();

  // put your main code here, to run repeatedly:
}