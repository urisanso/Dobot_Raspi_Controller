#!/usr/bin/env python3
import cv2
import os
import argparse
from time import sleep

# =======================
# Argumentos
# =======================
parser = argparse.ArgumentParser(description="Captura de dataset con cámara Dobot/Raspi")
parser.add_argument("--label", required=True, help="Nombre del objeto o clase a fotografiar")
parser.add_argument("--n", type=int, required=True, help="Cantidad de imágenes a capturar")
parser.add_argument("--interval", type=float, default=0.5, help="Intervalo entre fotos (s)")
parser.add_argument("--cam", type=int, default=0, help="Índice de cámara (0 por defecto)")
args = parser.parse_args()

# =======================
# Configuración inicial
# =======================
output_dir = os.path.join("dataset", args.label)
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(args.cam)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")

print(f"📸 Capturando {args.n} imágenes para '{args.label}'...")
count = 0

# =======================
# Bucle de captura
# =======================
while count < args.n:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Error al leer frame")
        break

    # Mostrar vista previa
    cv2.imshow("Vista previa", frame)

    # Guardar imagen
    filename = os.path.join(output_dir, f"{args.label}_{count:03d}.jpg")
    cv2.imwrite(filename, frame)
    print(f"✅ Guardada: {filename}")
    count += 1

    # Esperar un intervalo
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    sleep(args.interval)

cap.release()
cv2.destroyAllWindows()
print("✅ Captura completada.")
