#include <Arduino.h>
#include <AccelStepper.h>

// ================== PINES ==================
#define LDR_PIN 34
#define RPI_EN_PIN 32
#define LED_BUILTIN 2
#define PIN_PULSADOR 27       // <-- PIN del pulsador (con pull-up interno)

const int PIN_DIR  = 13;
const int PIN_STEP = 12;
const int PIN_EN   = 14;

// ================== MOTOR ==================
const int STEPS_PER_REV = 200;
const int MICROSTEPS    = 1;

const float RPM_MAX = 30.0;
const float RAMP_TIME_S = 0.5;

// ================== LDR ==================
const int UMBRAL_ALTO = 2200; // luz clara → arranca
const int UMBRAL_BAJO = 1800; // oscuridad → frena

bool cintaActiva = false;

// ================== PULSADOR ==================
bool sistemaPausado = false;       // true = pausado por el operador
bool estadoAnteriorBtn = HIGH;     // para detectar flanco descendente
unsigned long ultimoDebounce = 0;
const unsigned long DEBOUNCE_MS = 500;

// ================== STEPPER ==================
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEP, PIN_DIR);

// ================== FUNCIONES ==================
float rpmToStepsPerSecond(float rpm, int microsteps, int steps_per_rev = 200) {
    return (rpm * steps_per_rev * microsteps) / 60.0;
}

// ================== SETUP ==================
void setup() {
    Serial.begin(115200);

    pinMode(RPI_EN_PIN, OUTPUT);
    digitalWrite(RPI_EN_PIN, LOW);
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    pinMode(PIN_EN, OUTPUT);
    digitalWrite(PIN_EN, LOW);

    pinMode(PIN_PULSADOR, INPUT_PULLUP);  // Pull-up interno: reposo = HIGH, pulsado = LOW

    float maxSpeedSteps = rpmToStepsPerSecond(RPM_MAX, MICROSTEPS, STEPS_PER_REV);
    float accelSteps = maxSpeedSteps / RAMP_TIME_S;

    stepper.setMaxSpeed(maxSpeedSteps);
    stepper.setAcceleration(accelSteps);
    stepper.setCurrentPosition(0);

    Serial.println("Sistema con histéresis listo");
}

// ================== LOOP ==================
void loop() {
    // ======== LECTURA PULSADOR CON DEBOUNCE ========
    bool estadoBtn = digitalRead(PIN_PULSADOR);

    if (estadoAnteriorBtn == HIGH && estadoBtn == LOW) {       // flanco descendente
        if (millis() - ultimoDebounce > DEBOUNCE_MS) {
            ultimoDebounce = millis();

            sistemaPausado = !sistemaPausado;

            if (sistemaPausado) {
                stepper.stop();
                Serial.println("⏸ PAUSA manual");
            } else {
                // Si al reanudar la cinta estaba activa por LDR, retoma movimiento
                if (cintaActiva) {
                    stepper.moveTo(stepper.currentPosition() + 1000000L);
                    Serial.println("▶ REANUDA movimiento");
                } else {
                    Serial.println("▶ REANUDA (esperando LDR)");
                }
            }
        }
        estadoAnteriorBtn = estadoBtn;
    }

    if (estadoAnteriorBtn == LOW && estadoBtn == HIGH) estadoAnteriorBtn = estadoBtn;
    

    // Si está detenida → solo arranca con UMBRAL_ALTO
    if (!sistemaPausado) {
        // ======== LDR ========
        int valorLDR = analogRead(LDR_PIN);

        Serial.print("LDR: ");
        Serial.println(valorLDR);

        // El enable de la RPi y el LED reflejan si la cinta está corriendo
        bool cintatCorriendo = cintaActiva && !sistemaPausado;
        digitalWrite(RPI_EN_PIN, !cintatCorriendo);
        digitalWrite(LED_BUILTIN, !cintatCorriendo);

        // ======== LOGICA CON HISTERESIS ========
        if (!cintaActiva && valorLDR > UMBRAL_ALTO) {
            cintaActiva = true;

            long bigTarget = 1000000L;
            stepper.moveTo(stepper.currentPosition() + bigTarget);

            Serial.println("CINTA ARRANCA");
        }

        // Si está en movimiento → solo frena con UMBRAL_BAJO
        if (cintaActiva && valorLDR < UMBRAL_BAJO) {
            cintaActiva = false;

            stepper.stop();
            Serial.println("OBJETO DETECTADO - CINTA FRENA");
        }
    }

    stepper.run();
}