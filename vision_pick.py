#!/usr/bin/env python3
import cv2
import numpy as np
import time
from pydobot import Dobot
import dobot_utils as du

# =================== CONFIGURACIÓN ===================
COLOR = "red"               # "red" | "blue" | "green"

# Refs dadas por vos (como % de la resolución)
CX_REF_PCT = 0.750           # 50% del ancho
CY_REF_PCT = 0.5           # 75% del alto

# Tolerancias
CENTER_TOL_COARSE_X = 40    # px: centrado "grosso" en X con J1
CENTER_TOL_FINE_X   = 8     # px: fine X
CENTER_TOL_FINE_Y   = 8     # px: fine Y

# Giro de búsqueda (J1)
VEL_J1_GIRO      = -3.0     # grados/step durante búsqueda
VEL_J1_CENTRADO  = 1.0      # grados/step durante centrado con J1
SLEEP_STEP       = 0.10     # s entre pasos

# Ganancias y límites de X/Y (mm)
KX_MM_PER_PX = 0.05
KY_MM_PER_PX = 0.05
MAX_STEP_X   = 2.0
MAX_STEP_Y   = 2.0
MIN_STEP_X   = 0.4
MIN_STEP_Y   = 0.4

# Invierte ejes si corrige al revés
INV_X = False
INV_Y = False

# Alturas y tiempos
Z_PICK        = -50
SUCTION_TIME  = 1.0

# Límites (seguridad)
J1_MIN, J1_MAX = -100.0, 100.0
X_MIN, X_MAX   =  50.0, 300.0
Y_MIN, Y_MAX   = -150.0, 150.0

# =================== DETECCIÓN DE COLOR ===================
def detectar_centro_color(frame, color="red"):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if color == "red":
        mask1 = cv2.inRange(hsv, (0,120,70), (10,255,255))
        mask2 = cv2.inRange(hsv, (170,120,70), (180,255,255))
        mask = cv2.bitwise_or(mask1, mask2)
    elif color == "blue":
        mask = cv2.inRange(hsv, (100,150,0), (140,255,255))
    elif color == "green":
        mask = cv2.inRange(hsv, (35,100,100), (85,255,255))
    else:
        return None
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] > 0:
            cx = int(M["m10"]/M["m00"])
            cy = int(M["m01"]/M["m00"])
            return (cx, cy)
    return None

def clamp(v, vmin, vmax):
    return max(vmin, min(v, vmax))

def step_px_to_mm(k_mm_per_px, err_px, max_step, min_step):
    e = abs(err_px)
    if e > 40:
        base = max_step
    elif e > 15:
        base = max_step * 0.6
    else:
        base = max(max_step * 0.3, min_step)
    return np.clip(k_mm_per_px * err_px, -base, base)

# =================== MAIN ===================
def main():
    # Conexión robot y home físico
    puerto = du.detectar_puerto()
    if not puerto:
        raise RuntimeError("⚠️ No se detectó el Dobot por USB.")
    device = Dobot(port=puerto, verbose=False)
    du.clear_alarm(device)
    du.home_fisico(device)

    # Cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("⚠️ No se pudo abrir la cámara.")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cx_ref = CX_REF_PCT * width
    cy_ref = CY_REF_PCT * height
    print(f"📏 {width}x{height} | refs: cx_ref={cx_ref:.1f}, cy_ref={cy_ref:.1f}")

    # Pose inicial
    x, y, z, r, j1, j2, j3, j4 = device.pose()

    # ========== ETAPA 1: BÚSQUEDA GIRANDO J1 ==========
    print(f"🔎 Búsqueda de {COLOR} girando J1...")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        centro = detectar_centro_color(frame, COLOR)
        if centro:
            print("🟥 Detectado → centrado coarse con J1")
            break
        j1_next = clamp(j1 + VEL_J1_GIRO, J1_MIN, J1_MAX)
        if abs(j1_next - j1) < 1e-3:
            print("⚠️ Límite J1 en búsqueda. Salgo.")
            break
        j1 = j1_next
        du.move_joints(device, j1, j2, j3, j4, wait=False)
        time.sleep(SLEEP_STEP)

    # ========== ETAPA 2: COARSE (J1 → X) ==========
    print(f"🎯 Coarse J1 hacia cx_ref ±{CENTER_TOL_COARSE_X}px")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        centro = detectar_centro_color(frame, COLOR)
        if not centro:
            print("⚠️ Se perdió el bloque en COARSE. Salgo.")
            break
        cx, cy = centro
        err_x = cx - cx_ref
        print(f"[COARSE] cx={cx:.1f}  err_x={err_x:.1f}px  | J1={j1:.1f}")
        if abs(err_x) < CENTER_TOL_COARSE_X:
            print("🟢 Coarse OK → Fine X")
            break
        j1 += (-VEL_J1_CENTRADO if err_x > 0 else VEL_J1_CENTRADO)
        j1 = clamp(j1, J1_MIN, J1_MAX)
        du.move_joints(device, j1, j2, j3, j4, wait=False)
        time.sleep(SLEEP_STEP)

    # ========== ETAPA 3: FINE X (sólo X) ==========
    print(f"🧩 Fine X hasta |err_x|<{CENTER_TOL_FINE_X}px")
    x, y, z, r, *_ = device.pose()
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        centro = detectar_centro_color(frame, COLOR)
        if not centro:
            print("⚠️ Se perdió el bloque en FINE X. Salgo.")
            break
        cx, cy = centro
        err_x = cx - cx_ref
        # paso adaptativo en X
        dx = step_px_to_mm(KX_MM_PER_PX, err_x, MAX_STEP_X, MIN_STEP_X)
        if INV_X: dx = -dx
        print(f"[FINE X] cx={cx:.1f} err_x={err_x:.1f}px  dx={dx:+.2f}mm  | X={x:.1f}")
        if abs(err_x) < CENTER_TOL_FINE_X:
            print("✅ Fine X OK → Fine Y")
            break
        x = clamp(x + dx, X_MIN, X_MAX)
        du.move_to_xyzr(device, x, y, z, r, wait=True)
        time.sleep(SLEEP_STEP)

    # ========== ETAPA 4: FINE Y (sólo Y) ==========
    print(f"🧩 Fine Y hasta |err_y|<{CENTER_TOL_FINE_Y}px")
    x, y, z, r, *_ = device.pose()
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        centro = detectar_centro_color(frame, COLOR)
        if not centro:
            print("⚠️ Se perdió el bloque en FINE Y. Salgo.")
            break
        cx, cy = centro
        err_y = cy - cy_ref
        # paso adaptativo en Y
        dy = step_px_to_mm(KY_MM_PER_PX, err_y, MAX_STEP_Y, MIN_STEP_Y)
        if INV_Y: dy = -dy
        print(f"[FINE Y] cy={cy:.1f} err_y={err_y:.1f}px  dy={dy:+.2f}mm  | Y={y:.1f}")
        if abs(err_y) < CENTER_TOL_FINE_Y:
            print("✅ Fine Y OK → pick")
            break
        y = clamp(y + dy, Y_MIN, Y_MAX)
        du.move_to_xyzr(device, x, y, z, r, wait=True)
        time.sleep(SLEEP_STEP)

    cap.release()

    # ========== ETAPA 5: PICK ==========
    x, y, z_now, r, *_ = device.pose()
    du.move_to_xyzr(device, x, y, Z_PICK, r, wait=True)
    du.suck(device, True)
    time.sleep(SUCTION_TIME)
    du.move_to_xyzr(device, x, y, z_now, r, wait=True)
    du.suck(device, False)

    print("🏁 Listo.")
    device.close()

if __name__ == "__main__":
    main()
