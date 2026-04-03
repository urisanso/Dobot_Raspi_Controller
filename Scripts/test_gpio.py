import RPi.GPIO as GPIO
import time

# --- CONFIGURACIÓN ---
# Usamos numeración BCM (la de los nombres de los pines, no la posición física)
PIN_ENTRADA = 26 

def setup():
    GPIO.setmode(GPIO.BCM)
    # Configuramos con PULL_DOWN interna para que si el cable está al aire, lea 0
    GPIO.setup(PIN_ENTRADA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    print(f"--- Test de GPIO {PIN_ENTRADA} iniciado ---")
    print("Presioná Ctrl+C para salir")

def loop():
    try:
        while True:
            # Leemos el estado del pin
            estado = GPIO.input(PIN_ENTRADA)
            
            if estado == GPIO.HIGH:
                print("🟢 ESTADO ALTO (3.3V) - Señal del ESP32 detectada")
            else:
                print("🔴 ESTADO BAJO (0V) - Sin señal")
            
            # Un pequeño delay para no saturar la terminal
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest finalizado por el usuario.")
    finally:
        # Limpiamos la configuración para no dejar pines "sucios"
        GPIO.cleanup()
        print("GPIO Cleaned up. Chau!")

if __name__ == "__main__":
    setup()
    loop()