#!/usr/bin/env python3
import time, curses
from dobot_utils import (
    detectar_puerto, crear_archivo_trayectoria,
    append_trayectoria, reproducir_trayectoria, suck
)
from pydobot import Dobot, enums

INTERVALO = 0.5
STEP_JOINT = 3.0  # grados por tecla

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
    joints = [0, 0, 0, 0]
    bomba_activa = 0

    pose = device.pose()
    x, y, z, r = pose[0], pose[1], pose[2], pose[3]
    modo_cartesiano = False
    STEP_CART = 5.0  # mm por paso


    while True:
        key = stdscr.getch()
        moved = False

        # === SALIR ===
        if key == ord('q'):
            break

        # === CONTROL DE ESTADO ===
        elif key == ord('g'):
            grabando = not grabando
            msg = "⏺ Grabando..." if grabando else "⏹ Grabación pausada"
        elif key == ord('c'):
            archivo_actual = crear_archivo_trayectoria()
            n_puntos = 0
            msg = "🧹 Archivo nuevo creado"
        elif key == ord('t'):
            msg = "▶️ Reproduciendo..."
            stdscr.addstr(8, 0, msg)
            stdscr.refresh()
            reproducir_trayectoria(device, archivo_actual)
            msg = "✅ Reproducción terminada"
        elif key == ord('b'):
            bomba_activa = 1 - bomba_activa
            suck(device, bomba_activa)
            msg = f"💨 Bomba {'ON' if bomba_activa else 'OFF'}"

        # === CONTROL DE MOVIMIENTO ===
        if key == ord('m'):
            modo_cartesiano = not modo_cartesiano
            msg = f"🔄 Modo {'CARTESIANO' if modo_cartesiano else 'JOINT'}"

        moved = False

        try:
            pose = device.pose()
            if not pose:
                continue
            # siempre sincronizamos antes de mover
            x, y, z, r = pose[0], pose[1], pose[2], pose[3]
            joints = [pose[4], pose[5], pose[6], pose[7]]
        except Exception:
            continue  # si está en modo manual o no responde, no hacer nada

        if modo_cartesiano:
            if key == ord('w'): x += STEP_CART; moved = True
            if key == ord('s'): x -= STEP_CART; moved = True
            if key == ord('a'): y += STEP_CART; moved = True
            if key == ord('d'): y -= STEP_CART; moved = True
            if key == ord('r'): z += STEP_CART; moved = True
            if key == ord('f'): z -= STEP_CART; moved = True
            if key == ord('e'): r += STEP_CART; moved = True
            if key == ord('x'): r -= STEP_CART; moved = True

            if moved:
                device.move_to(x, y, z, r, wait=False)
                msg = f"→ XYZR ({x:.1f},{y:.1f},{z:.1f},{r:.1f})"

        else:
            if key == ord('w'): joints[0] += STEP_JOINT; moved = True
            if key == ord('s'): joints[0] -= STEP_JOINT; moved = True
            if key == ord('a'): joints[1] += STEP_JOINT; moved = True
            if key == ord('d'): joints[1] -= STEP_JOINT; moved = True
            if key == ord('e'): joints[2] += STEP_JOINT; moved = True
            if key == ord('x'): joints[2] -= STEP_JOINT; moved = True
            if key == ord('r'): joints[3] += STEP_JOINT; moved = True
            if key == ord('f'): joints[3] -= STEP_JOINT; moved = True

            if moved:
                device._set_ptp_cmd(
                    x=joints[0], y=joints[1], z=joints[2], r=joints[3],
                    mode=enums.PTPMode.MOVJ_ANGLE,
                    wait=False
                )
                msg = f"→ Joints {tuple(round(j,1) for j in joints)}"

        # === GRABACIÓN AUTOMÁTICA ===
        if grabando and (time.time() - t0 >= INTERVALO):
            try:
                pose = device.pose()
                if not pose:
                    continue
                j1, j2, j3, j4 = pose[4:8]
            except Exception:
                continue  # ignora si no puede leer pose

            if ultimo is None or any(abs(a - b) > 0.05 for a, b in zip((j1, j2, j3, j4), ultimo)):
                n_puntos += 1
                append_trayectoria(
                    archivo_actual, j1, j2, j3, j4,
                    punto=f"P{n_puntos}", bomba=bomba_activa
                )
                ultimo = (j1, j2, j3, j4)
                msg = f"💾 Guardado P{n_puntos} (bomba={bomba_activa})"
            t0 = time.time()

        # === UI ===
        stdscr.clear()
        stdscr.addstr(0, 0, "=== DOBOT - GRABADOR DE TRAYECTORIAS ===")
        stdscr.addstr(1, 0, f"Puerto: {port}")
        stdscr.addstr(2, 0, f"Grabando: {'Sí' if grabando else 'No'}")
        stdscr.addstr(3, 0, f"Bomba: {'ON' if bomba_activa else 'OFF'}")
        stdscr.addstr(4, 0, f"Puntos guardados: {n_puntos}")
        stdscr.addstr(6, 0, msg)
        stdscr.addstr(8, 0, "Controles: G grabar | T reproducir | C nuevo | B bomba | Q salir")
        stdscr.addstr(10, 0, "Movimientos: W/S J1 | A/D J2 | E/X J3 | R/F J4")
        stdscr.refresh()
        time.sleep(0.05)

    device.close()
    stdscr.clear()
    stdscr.addstr(0, 0, "Dobot desconectado. Fin del programa.")
    stdscr.refresh(); time.sleep(0.05)

if __name__ == "__main__":
    curses.wrapper(main)
