#!/usr/bin/env python3
import time
import curses
import serial.tools.list_ports
from pydobot import Dobot, enums

# ------------------- CONFIGURACIÓN -------------------
STEP = 2  # grados por pulsación
DELAY = 0.05  # segundos entre comandos

# ------------------- CONEXIÓN ------------------------
ports = [p.device for p in serial.tools.list_ports.comports()
         if 'USB' in p.description or 'ACM' in p.device]
if not ports:
    raise Exception("❌ No se encontró ningún Dobot conectado.")
port = ports[0]

device = Dobot(port=port)
print(f"✅ Conectado al Dobot en {port}")

# posición articular actual estimada
joints = [0, 0, 0, 0]

# ------------------- FUNCIONES ------------------------
def move_joints():
    """Envía los ángulos actuales al Dobot."""
    device._set_ptp_cmd(
        x=joints[0], y=joints[1], z=joints[2], r=joints[3],
        mode=enums.PTPMode.MOVJ_ANGLE,
        wait=False
    )

def status_msg(stdscr):
    stdscr.addstr(0, 0, f"Joint1={joints[0]:>5.1f} | Joint2={joints[1]:>5.1f} | Joint3={joints[2]:>5.1f} | Joint4={joints[3]:>5.1f}")
    stdscr.addstr(2, 0, "Controles:")
    stdscr.addstr(3, 0, "  Joint1: Q / A")
    stdscr.addstr(4, 0, "  Joint2: W / S")
    stdscr.addstr(5, 0, "  Joint3: E / D")
    stdscr.addstr(6, 0, "  Joint4: R / F")
    stdscr.addstr(8, 0, "  Z: volver a 0   |   X: salir")
    stdscr.refresh()

# ------------------- LOOP PRINCIPAL -------------------
def main(stdscr):
    curses.cbreak()
    stdscr.nodelay(True)
    stdscr.clear()

    status_msg(stdscr)
    while True:
        key = stdscr.getch()
        if key == -1:
            time.sleep(DELAY)
            continue

        # Joint1
        if key in [ord('q'), ord('Q')]:
            joints[0] += STEP
        elif key in [ord('a'), ord('A')]:
            joints[0] -= STEP
        # Joint2
        elif key in [ord('w'), ord('W')]:
            joints[1] += STEP
        elif key in [ord('s'), ord('S')]:
            joints[1] -= STEP
        # Joint3
        elif key in [ord('e'), ord('E')]:
            joints[2] += STEP
        elif key in [ord('d'), ord('D')]:
            joints[2] -= STEP
        # Joint4 (rotación final)
        elif key in [ord('r'), ord('R')]:
            joints[3] += STEP
        elif key in [ord('f'), ord('F')]:
            joints[3] -= STEP
        # Reset
        elif key in [ord('z'), ord('Z')]:
            joints[:] = [0, 0, 0, 0]
        # Salir
        elif key in [ord('x'), ord('X')]:
            break

        move_joints()
        stdscr.clear()
        status_msg(stdscr)
        time.sleep(DELAY)

    stdscr.addstr(10, 0, "👋 Saliendo y cerrando conexión...")
    stdscr.refresh()
    time.sleep(1)

# ------------------- EJECUCIÓN ------------------------
curses.wrapper(main)
device.close()
print("✅ Conexión cerrada.")
