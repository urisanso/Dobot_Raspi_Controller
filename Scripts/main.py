import numpy as np
import time
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


def main(device):

    # 1️⃣ Cargar matriz H y pose de visión
    H, vision_pose = load_homography(H_JSON)

    # 2️⃣ Ir a posición de búsqueda
    move_to_xyzr_joint(
        device,
        vision_pose["x"],
        vision_pose["y"],
        vision_pose["z"],
        vision_pose["r"]
    )

    suck(device, False)

    # 3️⃣ Detectar objetos
    detections, _ = detect_objects(
        api_key=API_KEY,
        project=PROJECT,
        version=VERSION,
        save_debug=True
    )

    # Mostrar todas las detecciones válidas
    detecciones_validas = imprimir_detecciones(
        detections,
        min_conf=CONFIDENCE_MIN,
        ignore_classes=IGNORE_CLASSES
    )

    if not detecciones_validas:
        print("❌ No hay objetos válidos")
        suck(device, True)
        return


    # # Elegir la de mayor porcentaje
    # target = elegir_mejor_deteccion(
    #     detections,
    #     min_conf=CONFIDENCE_MIN,
    #     ignore_classes=IGNORE_CLASSES
    # )

    # clase = target["class"]
    # conf = target["confidence"]
    # u, v = target["x"], target["y"]

    # print("\n=== OBJETIVO SELECCIONADO ===")
    # print(f"Clase: {clase}")
    # print(f"Confianza: {conf*100:.2f}%")
    # print(f"Centro BB: u={u}, v={v}")

    # # 5️⃣ Pixel → Robot
    # x, y = pixel_to_robot(u, v, H)
    # print(f"🤖 Destino robot: x={x:.2f}, y={y:.2f}")


    target = elegir_deteccion_mas_derecha(
        detections,
        H,
        min_conf=CONFIDENCE_MIN,
        ignore_classes=IGNORE_CLASSES
    )

    if target is None:
        print("❌ No hay objetos válidos")
        suck(device, True)
        return

    clase = target["class"]
    conf = target["confidence"]
    u, v = target["x"], target["y"]
    x, y = target["x_robot"], target["y_robot"]

    print("\n=== OBJETIVO SELECCIONADO ===")
    print(f"Clase: {clase}")
    print(f"Confianza: {conf*100:.2f}%")
    print(f"Centro BB: u={u}, v={v}")
    print(f"Más a la derecha => y_robot={y:.2f}")
    print(f"🤖 Destino robot: x={x:.2f}, y={y:.2f}")

    Xr_corr = x - 15 
    Yr_corr = y - 20

    # 6️⃣ Mover al objeto
    move_to_xyzr(
        device,
        Xr_corr,
        Yr_corr,
        Z_PICK,
        vision_pose["r"]
    )

    suck(device, True)

    time.sleep(1)

    places = load_places("JSON/places.json")
    place = places.get(clase, places["default"])
    print(f"📦 Place para {clase}: {place}")

    Z_SAFE = 80

    # subir antes de mover
    move_to_xyzr(device, Xr_corr, Yr_corr, Z_SAFE, vision_pose["r"])

    # ir a zona place arriba
    move_to_xyzr_joint(device, place["x"], place["y"], Z_SAFE, place["r"])

    # bajar
    move_to_xyzr(device, place["x"], place["y"], place["z"], place["r"])

    # soltar
    suck(device, False)

    time.sleep(0.5)

    # subir
    move_to_xyzr(device, place["x"], place["y"], Z_SAFE, place["r"])

    # 2️⃣ Ir a posición de búsqueda
    move_to_xyzr_joint(
        device,
        vision_pose["x"],
        vision_pose["y"],
        vision_pose["z"],
        vision_pose["r"]
    )


if __name__ == "__main__":
    from pydobot import Dobot

    port = detectar_puerto()
    device = Dobot(port=port, verbose=False)
    main(device)