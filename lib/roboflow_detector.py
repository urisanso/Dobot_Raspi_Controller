import cv2
import requests
from pathlib import Path
from datetime import datetime


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
