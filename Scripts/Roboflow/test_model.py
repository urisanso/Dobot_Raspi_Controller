#!/usr/bin/env python3
import cv2
from pathlib import Path
from datetime import datetime
from roboflow import Roboflow

# === CONFIGURACIÓN ===
rf = Roboflow(api_key="6CpctoE5C7mQOrwSaDWt")
project = rf.workspace("notengoidea").project("arcoiris-9o6ty")
model = project.version(2, local="http://localhost:9001/").model

SAVE_DIR = Path("predicciones")
SAVE_DIR.mkdir(exist_ok=True)
CAM_INDEX = 0  # cámara principal

# === CAPTURA ===
cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError("⚠️ No se pudo abrir la cámara")

ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError("⚠️ No se pudo capturar imagen")

# === GUARDAR FOTO ORIGINAL ===
filename = SAVE_DIR / f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
cv2.imwrite(str(filename), frame)
print(f"📷 Imagen guardada: {filename}")

# === INFERENCIA CON ROBOFLOW ===
result = model.predict(str(filename), confidence=40, overlap=30)
pred_path = SAVE_DIR / f"pred_{filename.name}"
result.save(str(pred_path))

print(f"✅ Detección completada: {pred_path.resolve()}")
