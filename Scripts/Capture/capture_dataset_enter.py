#!/usr/bin/env python3
import cv2
import os
import argparse
from time import sleep
from lib.utils import load_homography
from lib.dobot_utils import move_to_xyzr_joint, detectar_puerto
from pydobot import Dobot

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



port = detectar_puerto()
device = Dobot(port=port, verbose=False)
H, vision_pose = load_homography("JSON/Matriz_H.json")
print(vision_pose)
move_to_xyzr_joint(
    device,
    vision_pose["x"], vision_pose["y"],
    vision_pose["z"], vision_pose["r"]
)

cap = cv2.VideoCapture(args.cam)
if not cap.isOpened():
    raise RuntimeError(f"⚠️ No se pudo abrir la cámara en índice {args.cam}")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print(f"\n📸 Modo captura manual (ENTER) iniciado para '{args.label}'.")
print("➡️  Presioná [ENTER] para sacar una foto.")
print("➡️  Escribí 'q' y ENTER para salir.\n")

count = 0

# =======================
# Bucle de captura
# =======================
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("⚠️ Error al leer frame")
#         break

#     user_input = input("Presioná ENTER para capturar, o 'q' para salir: ").strip().lower()
#     if user_input == "q":
#         print("\n👋 Finalizando captura manual.")
#         break

#     filename = os.path.join(output_dir, f"{args.label}_{count:03d}.jpg")
#     cv2.imwrite(filename, frame)
#     print(f"✅ Foto guardada: {filename}")
#     count += 1
#     sleep(0.2)

while True:
    user_input = input("Presioná ENTER para capturar, o 'q' para salir: ").strip().lower()
    if user_input == "q":
        print("\n👋 Finalizando captura manual.")
        break

    # Vaciar el buffer descartando frames viejos
    for _ in range(5):
        cap.grab()

    # Ahora sí leer el frame fresco
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Error al leer frame")
        break

    filename = os.path.join(output_dir, f"{args.label}_{count:03d}.jpg")
    cv2.imwrite(filename, frame)
    print(f"✅ Foto guardada: {filename}")
    count += 1

cap.release()
print(f"✅ Total de imágenes capturadas: {count}")
