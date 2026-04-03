import numpy as np
import time
import RPi.GPIO as GPIO
from pathlib import Path

from lib.roboflow_detector import detect_objects
from lib.utils import load_homography, pixel_to_robot, get_bbox_centers
from lib.dobot_utils import (
    detectar_puerto, home_fisico, home_logico,
    suck, move_to_xyzr, move_joints, load_places, move_to_xyzr_joint
)

# === CONFIG ===
API_KEY = "6CpctoE5C7mQOrwSaDWt"
PROJECT = "model_ping_reduced"
VERSION = 2

Z_PICK = 43
CONFIDENCE_MIN = 0.8
IGNORE_CLASSES = ["vacio"]

H_JSON = Path("JSON/Matriz_H.json")

# --- CONFIG GPIO ---
PIN_ENTRADA_ESP = 26 
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_ENTRADA_ESP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 

def imprimir_detecciones(detections, min_conf=0.0, ignore_classes=None):
    """Muestra por pantalla todas las detecciones."""
    ignore_classes = ignore_classes or []

    print("\n=== DETECCIONES ===")
    validas = []

    for i, det in enumerate(detections, start=1):
        clase = det.get("class", "desconocida")
        conf = det.get("confidence", 0.0)

        if conf < min_conf:
            continue
        if clase in ignore_classes:
            continue

        x = det.get("x", None)
        y = det.get("y", None)
        w = det.get("width", None)
        h = det.get("height", None)

        print(
            f"[{i}] clase={clase} | "
            f"conf={conf*100:.2f}% | "
            f"centro=({x}, {y}) | "
            f"bbox=({w}, {h})"
        )

        validas.append(det)

    if not validas:
        print("No hay detecciones válidas.")

    return validas


def elegir_mejor_deteccion(detections, min_conf=0.0, ignore_classes=None):
    """Devuelve la detección válida con mayor confidence."""
    ignore_classes = ignore_classes or []

    validas = [
        det for det in detections
        if det.get("confidence", 0.0) >= min_conf
        and det.get("class", "") not in ignore_classes
    ]

    if not validas:
        return None

    return max(validas, key=lambda d: d.get("confidence", 0.0))

def elegir_deteccion_mas_derecha(detections, H, min_conf=0.0, ignore_classes=None):
    """
    Devuelve la detección válida más a la derecha.
    En este sistema: más a la derecha = menor Y en coordenadas robot.
    """
    ignore_classes = ignore_classes or []
    candidatas = []

    for det in detections:
        clase = det.get("class", "")
        conf = det.get("confidence", 0.0)

        if conf < min_conf:
            continue
        if clase in ignore_classes:
            continue

        u = det.get("x", None)
        v = det.get("y", None)
        if u is None or v is None:
            continue

        x_robot, y_robot = pixel_to_robot(u, v, H)

        det_ext = det.copy()
        det_ext["x_robot"] = x_robot
        det_ext["y_robot"] = y_robot
        candidatas.append(det_ext)

    if not candidatas:
        return None

    # más a la derecha = menor y_robot
    return min(candidatas, key=lambda d: d["y_robot"])

def actualizar_inventario(clase_detectada):
    archivo_path = "inventario.txt"
    inventario = {}

    # 1. Leer el archivo actual si existe
    if Path(archivo_path).exists():
        with open(archivo_path, "r") as f:
            for linea in f:
                if ":" in linea:
                    nombre, cantidad = linea.split(":")
                    inventario[nombre.strip()] = int(cantidad.strip())

    # 2. Incrementar el contador de la pieza detectada
    inventario[clase_detectada] = inventario.get(clase_detectada, 0) + 1

    # 3. Guardar los cambios
    with open(archivo_path, "w") as f:
        for nombre, cantidad in inventario.items():
            f.write(f"{nombre}: {cantidad}\n")
    
    print(f"📊 Inventario actualizado: {clase_detectada} ahora tiene {inventario[clase_detectada]}")


def main(device):
    # 1️⃣ Cargar matriz H y pose de visión (Fuera del loop para no leer disco cada vez)
    H, vision_pose = load_homography(H_JSON)
    places = load_places("JSON/places.json")
    Z_SAFE = 80

    print("🚀 Iniciando Loop Infinito de Clasificación...")

    while True:
        # 2️⃣ Asegurar posición de búsqueda y ventosa apagada
        move_to_xyzr_joint(
            device,
            vision_pose["x"],
            vision_pose["y"],
            vision_pose["z"],
            vision_pose["r"]
        )
        suck(device, False)

        # 🛑 EL FILTRO: Solo avanza si el pin 26 está en 1
        print("⏳ Esperando señal del ESP32...")
        while GPIO.input(PIN_ENTRADA_ESP) == GPIO.LOW:
            time.sleep(0.05)
        
        print("📸 ¡Pieza detectada! Procesando...")

        # 3️⃣ Detectar objetos
        print("\n📸 Capturando imagen y detectando...")
        detections, _ = detect_objects(
            api_key=API_KEY,
            project=PROJECT,
            version=VERSION,
            save_debug=True
        )

        # 4️⃣ Filtrar y seleccionar
        target = elegir_deteccion_mas_derecha(
            detections,
            H,
            min_conf=CONFIDENCE_MIN,
            ignore_classes=IGNORE_CLASSES
        )

        # === LÓGICA DE ESPERA SI NO HAY NADA ===
        if target is None:
            print("💤 No hay objetos válidos. Esperando 5 segundos para reintentar...")
            time.sleep(5)
            continue  # Vuelve al inicio del while para sacar otra foto

        # === SI LLEGAMOS ACÁ, HAY UN TARGET VÁLIDO ===
        clase = target["class"]
        conf = target["confidence"]
        u, v = target["x"], target["y"]
        x, y = target["x_robot"], target["y_robot"]

        print(f"✅ OBJETIVO DETECTADO: {clase} ({conf*100:.1f}%)")
        
        # Aplicamos tus correcciones de calibración
        Xr_corr = x - 0 
        Yr_corr = y - 20

        # 6️⃣ EJECUCIÓN DE PICK (Mover al objeto)
        move_to_xyzr(device, Xr_corr, Yr_corr, Z_PICK, vision_pose["r"])
        suck(device, True)
        time.sleep(1)

        # 7️⃣ EJECUCIÓN DE PLACE
        place = places.get(clase, places["default"])
        print(f"📦 Clasificando en: {clase}")

        # Trayectoria de seguridad: Subir -> Ir a zona -> Bajar -> Soltar
        move_to_xyzr(device, Xr_corr, Yr_corr, Z_SAFE, vision_pose["r"])
        move_to_xyzr_joint(device, place["x"], place["y"], Z_SAFE, place["r"])
        move_to_xyzr(device, place["x"], place["y"], place["z"], place["r"])
        
        suck(device, False)
        time.sleep(0.5)

        # --- NUEVO: GESTIÓN DE INVENTARIO ---
        actualizar_inventario(clase) 
        # ------------------------------------
        
        # Subir de nuevo para no chocar nada al volver
        move_to_xyzr(device, place["x"], place["y"], Z_SAFE, place["r"])
        
        print("🔄 Ciclo completado. Volviendo a posición de visión.")
        # El loop vuelve a empezar automáticamente

        # 🔄 Anti-repetición: Esperamos a que la señal baje antes de volver a mirar
        # while GPIO.input(PIN_ENTRADA_ESP) == GPIO.HIGH:
        #     time.sleep(0.1)

if __name__ == "__main__":
    from pydobot import Dobot

    port = detectar_puerto()
    device = Dobot(port=port, verbose=False)
    main(device)

