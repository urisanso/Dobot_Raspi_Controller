#!/usr/bin/env python3
import cv2, base64, requests, os
from pathlib import Path
from datetime import datetime

# === CONFIGURACIÓN ===
API_KEY = "rf_CdGfFS3yjidkwIVoKGy9ayUlXYI2"
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
filename = Path("predicciones") / f"captura_{timestamp}.jpg"
cv2.imwrite(str(filename), frame)
print(f"📷 Imagen capturada: {filename}")

# === ENVIAR A ROBOFLOW ===
url = f"https://detect.roboflow.com/{PROJECT}/{VERSION}?publishable_key={API_KEY}&confidence={CONFIDENCE}"
with open(filename, "rb") as f:
    response = requests.post(url, files={"file": f})

if response.status_code != 200:
    raise RuntimeError(f"❌ Error en la API: {response.status_code} - {response.text}")

# === GUARDAR RESULTADO ===
out_path = Path("predicciones") / f"pred_{timestamp}.jpg"
with open(out_path, "wb") as f:
    f.write(response.content)

print(f"✅ Resultado guardado: {out_path.resolve()}")
