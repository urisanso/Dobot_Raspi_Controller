import numpy as np
import time
import RPi.GPIO as GPIO
from pathlib import Path

from lib.roboflow_detector import (
    detect_objects, imprimir_detecciones, 
    elegir_mejor_deteccion, elegir_deteccion_mas_derecha
)
from lib.utils import (
    load_homography, pixel_to_robot, get_bbox_centers
    chequear_pulsador
)
from lib.dobot_utils import (
    detectar_puerto, home_fisico, home_logico,
    suck, move_to_xyzr, move_joints, load_places, move_to_xyzr_joint
)
from lib.inventario_utils import (
    buscar_ultimo_inventario, nuevo_nombre_inventario, 
    seleccionar_inventario, actualizar_inventario
)

# === CONFIG ===
API_KEY = "6CpctoE5C7mQOrwSaDWt"
PROJECT = "model_ping_reduced_v2-0" #model_ping_reduced_v2-0/2
VERSION = 2

Z_PICK = 43
CONFIDENCE_MIN = 0.8
IGNORE_CLASSES = ["vacio"]
MIN_Y_ROBOT = -20
MAX_Y_ROBOT = 45

H_JSON = Path("JSON/Matriz_H.json")

# --- CONFIG GPIO ---
PIN_ENTRADA_ESP = 26
PIN_PULSADOR    = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_ENTRADA_ESP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PIN_PULSADOR,    GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main(device):
    # 1️⃣ Cargar matriz H y pose de visión (Fuera del loop para no leer disco cada vez)
    H, vision_pose = load_homography(H_JSON)
    places = load_places("JSON/places.json")
    Z_SAFE = 80
    ciclo_activo = False

    print("🤖 Sistema listo. Presioná el botón para iniciar la clasificación.")

    try:
        while True:
            
            # ── MODO ESPERA ──────────────────────────────────────────────
            ciclo_activo = chequear_pulsador(ciclo_activo)
            if not ciclo_activo:
                time.sleep(0.1)   # idle liviano, sin quemar CPU
                continue

            # ── MODO ACTIVO ──────────────────────────────────────────────
            print("🚀 Ciclo activo...")

            move_to_xyzr_joint(
                device,
                vision_pose["x"], vision_pose["y"],
                vision_pose["z"], vision_pose["r"]
            )
            suck(device, False)

            # Señal del ESP32 (tu lógica original intacta)
            print("⏳ Esperando señal del ESP32...")
            while GPIO.input(PIN_ENTRADA_ESP) == GPIO.LOW:
                ciclo_activo = chequear_pulsador(ciclo_activo)
                if not ciclo_activo:          # ← salida rápida si paran mientras espera
                    print("⏹ Ciclo detenido durante espera de ESP32.")
                    break
                time.sleep(0.05)
            
            ciclo_activo = chequear_pulsador(ciclo_activo)
            if not ciclo_activo:
                continue

            print("📸 ¡Pieza detectada! Procesando...")

            detections, _ = detect_objects(
                api_key=API_KEY,
                project=PROJECT,
                version=VERSION,
                save_debug=True
            )

            target = elegir_deteccion_mas_derecha(
                detections, H,
                min_conf=CONFIDENCE_MIN,
                ignore_classes=IGNORE_CLASSES
            )

            if target is None:
                print("💤 No hay objetos válidos. Esperando 5 segundos...")
                time.sleep(5)
                continue

            clase = target["class"]
            conf  = target["confidence"]
            u, v  = target["x"], target["y"]
            x, y  = target["x_robot"], target["y_robot"]

            print(f"✅ OBJETIVO: {clase} ({conf*100:.1f}%)")

            Xr_corr = x - 0
            Yr_corr = y - 20

            move_to_xyzr(device, Xr_corr, Yr_corr, Z_PICK, vision_pose["r"])
            suck(device, True)
            time.sleep(1)

            place = places.get(clase, places["default"])
            print(f"📦 Clasificando en: {clase}")

            move_to_xyzr(device, Xr_corr, Yr_corr, Z_SAFE, vision_pose["r"])
            move_to_xyzr_joint(device, place["x"], place["y"], Z_SAFE, place["r"])
            move_to_xyzr(device, place["x"], place["y"], place["z"], place["r"])

            suck(device, False)
            time.sleep(0.5)

            actualizar_inventario(clase)

            move_to_xyzr(device, place["x"], place["y"], Z_SAFE, place["r"])
            print("🔄 Ciclo completado.")

    except KeyboardInterrupt:
        print("\n🛑 Interrupción manual (Ctrl+C).")

    finally:
        # Limpieza segura siempre, pase lo que pase
        suck(device, False)
        GPIO.cleanup()
        print("✅ GPIO liberado. Sistema apagado limpiamente.")

if __name__ == "__main__":
    from pydobot import Dobot

    port = detectar_puerto()
    device = Dobot(port=port, verbose=False)
    main(device)

