#include <Arduino.h>
#include <AccelStepper.h>

// ==== PINES ESP32 ====
// Botón entre D34 y 3V3, con resistor de 10k a GND.
// Eso significa: HIGH = apretado, LOW = suelto.
const int PIN_BTN  = 34;

const int PIN_DIR  = 13;
const int PIN_STEP = 12;
const int PIN_EN   = 14;   // A4988/DRV8825: LOW = enable, HIGH = disable

// ================== PARÁMETROS DEL MOTOR / DRIVER ==================
const int STEPS_PER_REV = 200;  // la mayoría de los NEMA: 200 pasos/rev
const int MICROSTEPS    = 1;    // 1, 2, 4, 8, 16... según M0/M1/M2

// ================== PARÁMETROS DE VELOCIDAD =========================
const float RPM_MAX = 30.0;     // RPM de crucero
// si quisieras usar RPM_MIN, lo podríamos usar para calcular otra rampa, pero
// con AccelStepper ya se encarga de acelerar desde 0 a RPM_MAX.
const float RPM_MIN = 10.0;     // (lo dejo por si querés jugar luego)

// Tiempo aproximado para alcanzar la velocidad (en segundos)
const float RAMP_TIME_S = 0.5;  // 0.5s para llegar a velocidad máxima

// ================== OBJETO AccelStepper =============================
// DRIVER = usa solo STEP + DIR
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEP, PIN_DIR);

// ================== VARIABLES DE ESTADO ============================
bool lastButtonPressed = false;   // estado anterior del botón
bool motorEnabled      = false;   // para manejar el PIN_EN

// ================== FUNCIONES AUXILIARES ===========================

// Convierte RPM a pasos por segundo
float rpmToStepsPerSecond(float rpm, int microsteps, int steps_per_rev = 200) {
    return (rpm * steps_per_rev * microsteps) / 60.0;
}

// Lee el pulsador: true = apretado, false = suelto
bool isButtonPressed() {
    // Botón va de D34 a 3V3 y tenés un pull-down a GND -> HIGH = apretado
    return (digitalRead(PIN_BTN) == HIGH);
}

void setup() {
    Serial.begin(9600);

    // Pines
    pinMode(PIN_BTN, INPUT);       // sin pull interno porque D34 no tiene
    pinMode(PIN_EN,  OUTPUT);

    // Al inicio, driver deshabilitado
    digitalWrite(PIN_EN, HIGH);    // HIGH = deshabilitado

    // Configuración base de AccelStepper
    float maxSpeedSteps = rpmToStepsPerSecond(RPM_MAX, MICROSTEPS, STEPS_PER_REV);
    // Aceleración en pasos/s^2 (aprox para tardar RAMP_TIME_S en llegar a maxSpeed)
    float accelSteps = maxSpeedSteps / RAMP_TIME_S;

    stepper.setMaxSpeed(maxSpeedSteps);
    stepper.setAcceleration(accelSteps);

    // Podemos empezar en posición 0
    stepper.setCurrentPosition(0);

    Serial.println("Driver con AccelStepper listo.");
    Serial.print("maxSpeedSteps: "); Serial.println(maxSpeedSteps);
    Serial.print("accelSteps: ");    Serial.println(accelSteps);
}

void loop() {
    bool buttonPressed = isButtonPressed();

    // Detectar flanco de subida: se apretó el botón (false -> true)
    if (buttonPressed && !lastButtonPressed) {
        Serial.println("Botón APRETADO: habilitar driver y arrancar movimiento.");

        // Habilitar driver
        digitalWrite(PIN_EN, LOW);   // LOW = habilitado
        motorEnabled = true;

        // Elegimos un objetivo lejano para que gire "infinito"
        // Por ejemplo, 1 millón de pasos hacia adelante.
        // Si querés cambiar sentido, podés usar un signo negativo.
        long bigTarget = -1000000L;
        stepper.moveTo(stepper.currentPosition() + bigTarget);
    }

    // Detectar flanco de bajada: se soltó el botón (true -> false)
    if (!buttonPressed && lastButtonPressed) {
        Serial.println("Botón SOLTADO: pedir frenado suave.");
        // stepper.stop() ajusta el target para frenar con la aceleración configurada
        stepper.stop();
        // NO deshabilitamos todavía el driver: dejamos que frene primero
    }

    // Llamar SIEMPRE a run() para que AccelStepper haga su magia
    stepper.run();

    // Si el botón está suelto y el motor ya terminó de frenar,
    // podemos deshabilitar el driver para que el motor quede "sueltito".
    if (!buttonPressed && motorEnabled && !stepper.isRunning()) {
        Serial.println("Motor detenido: deshabilitando driver.");
        digitalWrite(PIN_EN, HIGH);  // HIGH = deshabilitado
        motorEnabled = false;
    }

    lastButtonPressed = buttonPressed;
}

