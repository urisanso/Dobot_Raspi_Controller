#!/usr/bin/env python3
import cv2
import numpy as np
import time
from pydobot import Dobot
import dobot_utils as du

# =================== CONFIGURACIÓN ===================
COLOR = "red"           # color a detectar
CX_REF_PCT = 0.50       # referencia X (% de ancho)
CY_REF_PCT = 0.75       # referencia Y (% de alto)
REFRESH_TIME = 0.1      # segundos entre lecturas

# =================== DETECCIÓN DE COLOR ===================
def detectar_centro_color(frame, color="red"):
    """Devuelve el centro (cx, cy) del color indicado o None."""
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


# =================== PROGRAMA PRINCIPAL ===================
def main():
    # --- conectar al robot y hacer HOME físico ---
    puerto = du.detectar_puerto()
    if not puerto:
        raise RuntimeError("⚠️ No se detectó el Dobot por USB.")
    device = Dobot(port=puerto, verbose=False)
    du.clear_alarm(device)
    du.home_fisico(device)
    print("✅ Home físico ejecutado. Iniciando análisis visual...")

    # --- abrir cámara ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("⚠️ No se pudo abrir la cámara.")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cx_ref = CX_REF_PCT * width
    cy_ref = CY_REF_PCT * height
    print(f"📏 Resolución: {width}x{height}")
    print(f"🎯 Punto de referencia: ({cx_ref:.1f}, {cy_ref:.1f})")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            centro = detectar_centro_color(frame, COLOR)
            if centro:
                cx, cy = centro
                err_x = cx - cx_ref
                err_y = cy - cy_ref
                print(f"→ bbox(cx,cy)=({cx:4d},{cy:4d}) | err_x={err_x:7.2f}px | err_y={err_y:7.2f}px")
            else:
                print("⚠️ No se detecta el color seleccionado.")

            time.sleep(REFRESH_TIME)

    except KeyboardInterrupt:
        print("\n🛑 Finalizado por usuario.")
    finally:
        cap.release()
        device.close()


if __name__ == "__main__":
    main()
