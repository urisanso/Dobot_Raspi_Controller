#!/usr/bin/env python3
import time, curses, serial.tools.list_ports
from pydobot import Dobot
from dobot_utils import (
    home_fisico, home_logico, suck,
    move_to_xyzr, move_joints,
    save_points, load_points, clear_alarm
)

STEP_CART = 5    # mm por paso
STEP_JOINT = 3   # grados por paso
REFRESH_RATE = 0.1  # segundos entre lecturas de posición

# ==================== DETECCIÓN DE PUERTO ====================

def detectar_puerto():
    for p in serial.tools.list_ports.comports():
        if "USB" in p.device or "ACM" in p.device:
            return p.device
    return None

# ==================== MAIN LOOP ====================

def main(stdscr):
    stdscr.nodelay(True)
    stdscr.clear()
    stdscr.addstr(0, 0, "=== DOBOT MAGICIAN CONTROL === (Q salir)")

    port = detectar_puerto()
    if not port:
        stdscr.addstr(2, 0, "⚠️ No se detectó ningún Dobot.")
        stdscr.refresh(); time.sleep(2); return

    device = Dobot(port=port, verbose=False)
    stdscr.addstr(2, 0, f"✅ Conectado a {port}")

    puntos = load_points()
    last_update = 0
    action_msg = "Listo."

    while True:
        # Leer posición real periódicamente
        now = time.time()
        if now - last_update > REFRESH_RATE:
            pose = device.pose()
            x, y, z, r = pose[:4]
            j1, j2, j3, j4 = pose[4:8]
            last_update = now

        key = stdscr.getch()
        if key == -1:
            time.sleep(0.02)
            continue

        moved = False

        if key == ord('q'):
            break

        elif key == ord('h'):
            home_fisico(device); action_msg = "→ HOME físico"

        elif key == ord('j'):
            home_logico(device, puntos); action_msg = "→ HOME lógico"

        elif key == ord('g'):
            suck(device, True); action_msg = "→ Bomba ON"

        elif key == ord('b'):
            suck(device, False); action_msg = "→ Bomba OFF"

        elif key == ord('p'):
            nombre = f"P{len(puntos) + 1}"
            puntos[nombre] = [x, y, z, r]
            save_points(puntos); action_msg = f"💾 {nombre} guardado"

        elif key == ord('l'):
            puntos = load_points(); action_msg = "→ Puntos cargados"

        elif key == ord('c'):
            clear_alarm(device); action_msg = "→ Alarma limpiada"

        # === Movimiento cartesiano continuo ===
        elif key == ord('w'): move_to_xyzr(device, x + STEP_CART, y, z, r); action_msg = "→ +X"
        elif key == ord('s'): move_to_xyzr(device, x - STEP_CART, y, z, r); action_msg = "→ -X"
        elif key == ord('a'): move_to_xyzr(device, x, y + STEP_CART, z, r); action_msg = "→ +Y"
        elif key == ord('d'): move_to_xyzr(device, x, y - STEP_CART, z, r); action_msg = "→ -Y"
        elif key == ord('r'): move_to_xyzr(device, x, y, z + STEP_CART, r); action_msg = "→ +Z"
        elif key == ord('f'): move_to_xyzr(device, x, y, z - STEP_CART, r); action_msg = "→ -Z"
        elif key == ord('z'): move_to_xyzr(device, x, y, z, r + STEP_CART); action_msg = "→ +R"
        elif key == ord('x'): move_to_xyzr(device, x, y, z, r - STEP_CART); action_msg = "→ -R"

        # === Movimiento articular continuo ===
        elif key == ord('i'): move_joints(device, j1 + STEP_JOINT, j2, j3, j4); action_msg = "→ +J1"
        elif key == ord('k'): move_joints(device, j1 - STEP_JOINT, j2, j3, j4); action_msg = "→ -J1"
        elif key == ord('j'): move_joints(device, j1, j2 + STEP_JOINT, j3, j4); action_msg = "→ +J2"
        elif key == ord('l'): move_joints(device, j1, j2 - STEP_JOINT, j3, j4); action_msg = "→ -J2"
        elif key == ord('u'): move_joints(device, j1, j2, j3 + STEP_JOINT, j4); action_msg = "→ +J3"
        elif key == ord('o'): move_joints(device, j1, j2, j3 - STEP_JOINT, j4); action_msg = "→ -J3"
        elif key == ord('n'): move_joints(device, j1, j2, j3, j4 + STEP_JOINT); action_msg = "→ +J4"
        elif key == ord('m'): move_joints(device, j1, j2, j3, j4 - STEP_JOINT); action_msg = "→ -J4"

        elif key in range(ord('1'), ord('9') + 1):
            nombre = f"P{chr(key)}"
            if nombre in puntos:
                px, py, pz, pr = puntos[nombre]
                move_to_xyzr(device, px, py, pz, pr, wait=True)
                action_msg = f"→ Movido a {nombre}"
            else:
                action_msg = f"⚠️ {nombre} no existe"

        # UI
        stdscr.clear()
        stdscr.addstr(0, 0, "=== DOBOT MAGICIAN CONTROL ===")
        stdscr.addstr(1, 0, f"Puerto: {port}")
        stdscr.addstr(2, 0, f"XYZR: X={x:.1f}  Y={y:.1f}  Z={z:.1f}  R={r:.1f}")
        stdscr.addstr(3, 0, f"Joints: J1={j1:.1f}  J2={j2:.1f}  J3={j3:.1f}  J4={j4:.1f}")
        stdscr.addstr(5, 0, action_msg)
        stdscr.addstr(7, 0, "Controles: W/S X | A/D Y | R/F Z | Z/X R | I/K J1 | J/L J2 | U/O J3 | N/M J4")
        stdscr.addstr(9, 0, "H home físico | J home lógico | G/B bomba | P/L puntos | C clear | Q salir")
        stdscr.refresh()
        time.sleep(0.05)

    device.close()
    stdscr.clear()
    stdscr.addstr(0, 0, "Dobot desconectado. Fin del programa.")
    stdscr.refresh(); time.sleep(1.2)

if __name__ == '__main__':
    curses.wrapper(main)
