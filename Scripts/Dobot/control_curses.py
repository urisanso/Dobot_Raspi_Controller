import time
import curses
from pydobot import Dobot

def main(stdscr):
    stdscr.clear()
    stdscr.nodelay(True)  # no espera Enter
    stdscr.addstr(0, 0, "Control Dobot con flechas | Q para salir")

    device = Dobot(port='/dev/ttyACM1', verbose=False)
    device.ser.write(b'G28\n')
    device.ser.flush()
    time.sleep(5)

    x, y, z, r, *_ = device.pose()

    while True:
        key = stdscr.getch()
        moved = False

        if key == ord('q'):
            break
        elif key == ord('w'):
            x += 5; moved = True
        elif key == ord('s'):
            x -= 5; moved = True
        elif key == ord('a'):
            y += 5; moved = True
        elif key == ord('d'):
            y -= 5; moved = True
        elif key == ord('r'):
            z += 5; moved = True
        elif key == ord('f'):
            z -= 5; moved = True
        elif key == ord('z'):
            r += 5; moved = True
        elif key == ord('x'):
            r -= 5; moved = True

        if moved:
            try:
                device.move_to(x, y, z, r, wait=False)
                stdscr.addstr(2, 0, f"Moviendo a: X={x} Y={y} Z={z} R={r}    ")
            except Exception as e:
                stdscr.addstr(3, 0, f"Error: {str(e)}")

        stdscr.refresh()
        time.sleep(0.1)

    device.close()
    stdscr.addstr(5, 0, "Finalizado. Dobot desconectado.")
    stdscr.refresh()
    time.sleep(2)

# Ejecutar curses
curses.wrapper(main)
