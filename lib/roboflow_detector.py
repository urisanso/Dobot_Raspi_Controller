import cv2
import requests
from pathlib import Path
from datetime import datetime
from lib.utils import pixel_to_robot


def detect_objects(
    api_key,
    project,
    version,
    cam_index=0,
    confidence=40,
    save_debug=True,
):
    """
    Captura una imagen, ejecuta inferencia en Roboflow Serverless
    y devuelve las detecciones (JSON) y el frame original.
    """

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("No se pudo capturar imagen")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if save_debug:
        Path("capturas").mkdir(exist_ok=True)
        cv2.imwrite(f"capturas/captura_{timestamp}.jpg", frame)

    url = f"https://serverless.roboflow.com/{project}/{version}?api_key={api_key}&confidence={confidence}"

    _, img_encoded = cv2.imencode(".jpg", frame)
    response = requests.post(url, files={"file": img_encoded.tobytes()})

    if response.status_code != 200:
        raise RuntimeError(f"Roboflow error {response.status_code}: {response.text}")

    data = response.json()
    detections = data.get("predictions", [])

    if save_debug:
        debug = frame.copy()
        for p in detections:
            _draw_bbox(debug, p)

        Path("predicciones").mkdir(exist_ok=True)
        cv2.imwrite(f"predicciones/pred_{timestamp}.jpg", debug)

    return detections, frame


def _draw_bbox(image, prediction):
    x, y = int(prediction["x"]), int(prediction["y"])
    w, h = int(prediction["width"]), int(prediction["height"])
    label = prediction["class"]
    conf = prediction["confidence"]

    x1, y1 = int(x - w / 2), int(y - h / 2)
    x2, y2 = int(x + w / 2), int(y + h / 2)

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        image,
        f"{label} {conf:.2f}",
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
    )

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

def elegir_deteccion_mas_derecha(detections, H, min_conf=0.0, ignore_classes=None, miny_robot=-20, maxy_robot=20):
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

        print(f"clase= {clase}, x_robot= {x_robot}, y_robot= {y_robot}")

        if (y_robot < miny_robot) or (y_robot > maxy_robot):
            continue

        candidatas.append(det_ext)

    if not candidatas:
        return None

    # más a la derecha = menor y_robot
    return min(candidatas, key=lambda d: d["y_robot"])
