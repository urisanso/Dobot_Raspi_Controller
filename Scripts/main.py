import numpy as np
from pathlib import Path

from lib.roboflow_detector import detect_objects
from lib.dobot_utils import move_to_xyzr
from lib.utils import load_homography, pixel_to_robot, get_bbox_centers

# === CONFIG ===
API_KEY = "6CpctoE5C7mQOrwSaDWt"
PROJECT = "arcoiris-9o6ty"
VERSION = 2

Z_PICK = 0
CONFIDENCE_MIN = 0.5
IGNORE_CLASSES = ["vacio"]

H_JSON = Path("JSON/Matriz_H.json")

def main(device):

    # 1️⃣ Cargar matriz H y pose de visión
    H, vision_pose = load_homography(H_JSON)

    # 2️⃣ Ir a posición de búsqueda
    move_to_xyzr(
        device,
        vision_pose["x"],
        vision_pose["y"],
        vision_pose["z"],
        vision_pose["r"]
    )

    # 3️⃣ Detectar objetos
    detections, _ = detect_objects(
        api_key=API_KEY,
        project=PROJECT,
        version=VERSION,
        save_debug=True
    )

    centers = get_bbox_centers(
        detections,
        min_conf=CONFIDENCE_MIN,
        ignore_classes=IGNORE_CLASSES
    )

    if not centers:
        print("❌ No hay objetos válidos")
        return

    # 4️⃣ Tomar un objeto (por ahora el primero)
    target = centers[0]
    u, v = target["x"], target["y"]

    print(f"📸 Centro BB (imagen): u={u}, v={v}")

    # 5️⃣ Pixel → Robot
    x, y = pixel_to_robot(u, v, H)
    print(f"🤖 Destino robot: x={x:.2f}, y={y:.2f}")

    # 6️⃣ Mover al objeto
    move_to_xyzr(
        device,
        x,
        y,
        Z_PICK,
        vision_pose["r"]
    )


if __name__ == "__main__":
    from pydobot import Dobot

    device = Dobot(port="/dev/ttyUSB0")  # ajustá si hace falta
    main(device)