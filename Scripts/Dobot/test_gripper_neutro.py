#!/usr/bin/env python3
import time
import curses
import serial.tools.list_ports
from pydobot import Dobot

# === CONFIG ===
PIN_MIN = 10
PIN_MAX = 20


def detectar_puerto():
    for p in serial.tools.list_ports.comports():
        if "USB" in p.device or "ACM" in p.device:
            return p.device
    return None


def set_vacio(device):
    device._set_end_effector_suction_cup(enable=True)
    print("🟢 VACÍO (cerrar)")


def set_soplado(device):
    device._set_end_effector_suction_cup(enable=False)
    print("🔵 SOPLADO (abrir)")


def set_neutro(device):
    # apagar bomba
    device._set_end_effector_suction_cup(enable=False)

    # intentar apagar válvula con varios pines
    for pin in range(PIN_MIN, PIN_MAX):
        try:
            device._set_eio_level(pin, 0)
        except:
            pass

    print("🟡 NEUTRO (intentando apagar todo)")


def scan_pines(device, stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Escaneando pines... mirá el gripper 👀")

    for pin in range(PIN_MIN, PIN_MAX):
        try:
            device._set_eio_level(pin, 0)
            stdscr.addstr(2, 0, f"Pin {pin} -> 0")
            stdscr.refresh()
            time.sleep(0.8)

            device._set_eio_level(pin, 1)
            stdscr.addstr(3, 0, f"Pin {pin} -> 1")
            stdscr.refresh()
            time.sleep(0.8)

        except Exception as e:
            stdscr.addstr(5, 0, f"Error pin {pin}: {e}")
            stdscr.refresh()
            time.sleep(0.5)

    stdscr.addstr(7, 0, "Scan terminado. Presioná una tecla.")
    stdscr.refresh()
    stdscr.getch()


def main(stdscr):
    curses.cbreak()
    stdscr.nodelay(True)

    port = detectar_puerto()
    if not port:
        print("❌ No se encontró Dobot")
        return

    device = Dobot(port=port)
    print(f"✅ Conectado en {port}")

    stdscr.clear()
    stdscr.addstr(0, 0, "=== TEST GRIPPER ===")
    stdscr.addstr(2, 0, "1 → VACÍO (cerrar)")
    stdscr.addstr(3, 0, "2 → SOPLADO (abrir)")
    stdscr.addstr(4, 0, "3 → NEUTRO (intento real)")
    stdscr.addstr(5, 0, "P → Scan pines")
    stdscr.addstr(6, 0, "Q → salir")
    stdscr.refresh()

    while True:
        key = stdscr.getch()

        if key == ord('1'):
            set_vacio(device)

        elif key == ord('2'):
            set_soplado(device)

        elif key == ord('3'):
            set_neutro(device)

        elif key in [ord('p'), ord('P')]:
            scan_pines(device, stdscr)
            stdscr.clear()

        elif key in [ord('q'), ord('Q')]:
            break

        time.sleep(0.05)

    device.close()
    print("👋 Cerrado")


if __name__ == "__main__":
    curses.wrapper(main)