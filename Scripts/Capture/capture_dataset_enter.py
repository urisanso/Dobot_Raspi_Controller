#!/usr/bin/env python3
import cv2
import os
import argparse
from time import sleep

# =======================
# Argumentos
# =======================
parser = argparse.ArgumentParser(description="Captura manual con ENTER")
parser.add_argument("--label", required=True, help="Nombre del objeto o clase a fotografiar")
parser.add_argument("--cam", type=int, default=0, help="Índice de cámara (0 por defecto)")
args = parser.parse_args()

# =======================
# Configuración inicial
# =======================
output_dir = os.path.join("dataset", args.label)
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(args.cam)
if not cap.isOpened():
    raise RuntimeError(f"⚠️ No se pudo abrir la cámara en índice {args.cam}")

print(f"\n📸 Modo captura manual (ENTER) iniciado para '{args.label}'.")
print("➡️  Presioná [ENTER] para sacar una foto.")
print("➡️  Escribí 'q' y ENTER para salir.\n")

count = 0

# =======================
# Bucle de captura
# =======================
while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Error al leer frame")
        break

    user_input = input("Presioná ENTER para capturar, o 'q' para salir: ").strip().lower()
    if user_input == "q":
        print("\n👋 Finalizando captura manual.")
        break

    filename = os.path.join(output_dir, f"{args.label}_{count:03d}.jpg")
    cv2.imwrite(filename, frame)
    print(f"✅ Foto guardada: {filename}")
    count += 1
    sleep(0.2)

cap.release()
print(f"✅ Total de imágenes capturadas: {count}")
