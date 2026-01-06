#!/usr/bin/env python3
import cv2, base64, requests, os
from pathlib import Path
from datetime import datetime

# === CONFIGURACIÓN ===
API_KEY = "6CpctoE5C7mQOrwSaDWt"#"rf_CdGfFS3yiJdkwIVoKGy9ayUlXYI2"
WORKSPACE = "notengoidea"
PROJECT = "arcoiris-9o6ty"
VERSION = 2  # número de versión
CAM_INDEX = 0
CONFIDENCE = 40

# === CAPTURA ===
cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError("⚠️ No se pudo abrir la cámara")

ret, frame = cap.read()
cap.release()
if not ret:
    raise RuntimeError("⚠️ No se pudo capturar imagen")

Path("predicciones").mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = Path("capturas") / f"captura_{timestamp}.jpg"
cv2.imwrite(str(filename), frame)
print(f"📷 Imagen capturada: {filename}")

# === ENVIAR A ROBOFLOW ===
url = f"https://serverless.roboflow.com/{PROJECT}/{VERSION}?api_key={API_KEY}"
print(f"{url}")
with open(filename, "rb") as f:
    response = requests.post(url, files={"file": f})

if response.status_code != 200:
    raise RuntimeError(f"❌ Error en la API: {response.status_code} - {response.text}")

# === GUARDAR RESULTADO ===
out_path = Path("predicciones") / f"pred_{timestamp}.json"
with open(out_path, "wb") as f:
    f.write(response.content)

print(f"✅ Resultado guardado: {out_path.resolve()}")

data = response.json()
predictions = data["predictions"]

for p in predictions:
    x = int(p["x"])
    y = int(p["y"])
    w = int(p["width"])
    h = int(p["height"])
    label = p["class"]
    conf = p["confidence"]

    x1 = int(x - w / 2)
    y1 = int(y - h / 2)
    x2 = int(x + w / 2)
    y2 = int(y + h / 2)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        frame,
        f"({x},{y}) {label} {conf:.2f}",
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

out_path = Path("predicciones") / f"pred_{timestamp}.jpg"
cv2.imwrite(str(out_path), frame)
