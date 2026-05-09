#include <Arduino.h>

#define LDR_PIN 34

void setup() {
  Serial.begin(115200);
}

void loop() {
  int valor = analogRead(LDR_PIN);

  Serial.print("Valor LDR: ");
  Serial.println(valor);

  if (valor > 2000) {
    Serial.println("HAY LUZ");
  } else {
    Serial.println("NO HAY LUZ");
  }

  Serial.println("----");
  delay(500);
}