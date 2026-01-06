# control_dobot.py
import time, curses, serial.tools.list_ports
from pydobot import Dobot
from dobot_utils import home, suck, move_to_xyzr, move_joints, save_points, load_points, go_home, clear_alarm

STEP_CART = 5    # mm por paso
STEP_JOINT = 3   # grados por paso

def detectar_puerto():
    for p in serial.tools.list_ports.comports():
        if "USB" in p.device or "ACM" in p.device:
            return p.device
    return None

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
    pose = device.pose()
    # pose: (x, y, z, r, j1, j2, j3, j4) en el Magician común
    x, y, z, r = pose[0], pose[1], pose[2], pose[3]
    j1, j2, j3, j4 = pose[4], pose[5], pose[6], pose[7]

    modo_joint = False
    action_msg = "Modo cartesiano"

    while True:
        key = stdscr.getch()
        moved = False

        if key == ord('q'):
            break

        elif key == ord('t'):  # <--- CAMBIO DE MODO con T (ya no M)
            modo_joint = not modo_joint
            action_msg = "→ Modo JOINT" if modo_joint else "→ Modo CARTESIANO"

        elif key == ord('h'):
            home(device); action_msg = "→ HOME"

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

        # ===== CARTESIANO =====
        if not modo_joint:
            if key == ord('w'): x += STEP_CART; moved = True
            if key == ord('s'): x -= STEP_CART; moved = True
            if key == ord('a'): y += STEP_CART; moved = True
            if key == ord('d'): y -= STEP_CART; moved = True
            if key == ord('r'): z += STEP_CART; moved = True
            if key == ord('f'): z -= STEP_CART; moved = True
            if key == ord('z'): r += STEP_CART; moved = True
            if key == ord('x'): r -= STEP_CART; moved = True

            if moved:
                move_to_xyzr(device, x, y, z, r, wait=False)
                action_msg = f"→ XYZR ({x:.1f},{y:.1f},{z:.1f},{r:.1f})"

        # ===== JOINT =====
        else:
            if key == ord('i'): j1 += STEP_JOINT; moved = True
            if key == ord('k'): j1 -= STEP_JOINT; moved = True
            if key == ord('j'): j2 += STEP_JOINT; moved = True
            if key == ord('l'): j2 -= STEP_JOINT; moved = True
            if key == ord('u'): j3 += STEP_JOINT; moved = True
            if key == ord('o'): j3 -= STEP_JOINT; moved = True
            if key == ord('n'): j4 += STEP_JOINT; moved = True
            if key == ord('m'): j4 -= STEP_JOINT; moved = True  # ahora M es solo J4-

            if moved:
                move_joints(device, j1, j2, j3, j4)
                action_msg = f"→ Joints ({j1:.1f},{j2:.1f},{j3:.1f},{j4:.1f})"

        # Ir a puntos guardados
        if key in range(ord('1'), ord('9') + 1):
            nombre = f"P{chr(key)}"
            if nombre in puntos:
                px, py, pz, pr = puntos[nombre]
                move_to_xyzr(device, px, py, pz, pr, wait=True)
                x, y, z, r = px, py, pz, pr
                action_msg = f"→ Movido a {nombre}"
            else:
                action_msg = f"⚠️ {nombre} no existe"

        # UI
        stdscr.clear()
        stdscr.addstr(0, 0, "=== DOBOT MAGICIAN CONTROL ===")
        stdscr.addstr(1, 0, f"Puerto: {port}")
        stdscr.addstr(2, 0, "Modo: " + ("JOINT" if modo_joint else "CARTESIANO"))
        stdscr.addstr(3, 0, f"X={x:.1f} Y={y:.1f} Z={z:.1f} R={r:.1f}")
        stdscr.addstr(4, 0, f"J1={j1:.1f} J2={j2:.1f} J3={j3:.1f} J4={j4:.1f}")
        stdscr.addstr(6, 0, action_msg)
        stdscr.addstr(8, 0, "Q salir | T modo | G/B bomba | H home | P/L puntos | C clear")
        stdscr.refresh()
        time.sleep(0.08)

    device.close()
    stdscr.clear()
    stdscr.addstr(0, 0, "Dobot desconectado. Fin del programa.")
    stdscr.refresh(); time.sleep(1.2)

if __name__ == '__main__':
    curses.wrapper(main)
