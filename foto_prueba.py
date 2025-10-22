#!/usr/bin/env python3
import cv2
import time
from pathlib import Path

# === Configuración ===
CAM_INDEX = 0          # índice de cámara (probá 0, 1, 2... si no captura)
OUTPUT = Path("foto_prueba.jpg")

print("📷 Iniciando cámara...")

cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError(f"⚠️ No se pudo abrir la cámara en índice {CAM_INDEX}")

# Espera breve para estabilizar exposición
time.sleep(2)

ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError("⚠️ No se pudo capturar imagen del stream de video.")

cv2.imwrite(str(OUTPUT), frame)
print(f"✅ Imagen guardada correctamente en {OUTPUT.resolve()}")
