#!/usr/bin/env python3
import time, curses
from dobot_utils import (
    detectar_puerto, crear_archivo_trayectoria,
    append_trayectoria, reproducir_trayectoria
)
from pydobot import Dobot

INTERVALO = 0.5

def main(stdscr):
    stdscr.nodelay(True)
    stdscr.clear()
    stdscr.addstr(0, 0, "=== DOBOT - GRABADOR DE TRAYECTORIAS === (Q salir)")

    port = detectar_puerto()
    if not port:
        stdscr.addstr(2, 0, "❌ No se detectó ningún Dobot.")
        stdscr.refresh(); time.sleep(2); return

    device = Dobot(port=port, verbose=False)
    stdscr.addstr(2, 0, f"✅ Conectado a {port}")
    stdscr.refresh(); time.sleep(1)

    grabando = False
    archivo_actual = crear_archivo_trayectoria()
    ultimo = None
    n_puntos = 0
    t0 = time.time()
    msg = f"Archivo: {archivo_actual}"

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('g'):
            grabando = not grabando
            msg = "⏺ Grabando..." if grabando else "⏹ Grabación pausada"
        elif key == ord('c'):
            archivo_actual = crear_archivo_trayectoria()
            n_puntos = 0
            msg = "🧹 Archivo nuevo creado"
        elif key == ord('r'):
            msg = "▶️ Reproduciendo..."
            stdscr.addstr(8, 0, msg)
            stdscr.refresh()
            reproducir_trayectoria(device, archivo_actual)
            msg = "✅ Reproducción terminada"

        # === GRABACIÓN AUTOMÁTICA ===
        if grabando and (time.time() - t0 >= INTERVALO):
            pose = device.pose()
            j1, j2, j3, j4 = pose[4:8]
            if ultimo is None or any(abs(a - b) > 0.05 for a, b in zip((j1, j2, j3, j4), ultimo)):
                append_trayectoria(archivo_actual, j1, j2, j3, j4)
                ultimo = (j1, j2, j3, j4)
                n_puntos += 1
            t0 = time.time()

        # === INTERFAZ ===
        stdscr.clear()
        stdscr.addstr(0, 0, "=== DOBOT - GRABADOR DE TRAYECTORIAS ===")
        stdscr.addstr(1, 0, f"Puerto: {port}")
        stdscr.addstr(2, 0, f"Grabando: {'Sí' if grabando else 'No'}")
        stdscr.addstr(3, 0, f"Puntos guardados: {n_puntos}")
        stdscr.addstr(5, 0, msg)
        stdscr.addstr(7, 0, "G iniciar/parar | R reproducir | C nuevo archivo | Q salir")
        stdscr.refresh()
        time.sleep(0.05)

    device.close()
    stdscr.clear()
    stdscr.addstr(0, 0, "Dobot desconectado. Fin del programa.")
    stdscr.refresh(); time.sleep(1.2)

if __name__ == "__main__":
    curses.wrapper(main)
