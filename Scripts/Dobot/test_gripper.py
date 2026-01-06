import time, curses, serial.tools.list_ports
from pydobot import Dobot
from dobot_utils import detectar_puerto, gripper, suck
port = detectar_puerto()
if not port:
    print("⚠️ No se detectó ningún Dobot.")
    time.sleep(2)

d = Dobot(port=port, verbose=False)
print(f"✅ Conectado a {port}")

gripper(d, True)  # debería AGARRAR (vacío)
time.sleep(5)
gripper(d, False)  # debería ABRIR (soplar)
time.sleep(5)