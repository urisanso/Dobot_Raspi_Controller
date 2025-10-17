# dobot_raspi_controller.py
from DobotEDU import *
import time
import random  # simula red neuronal

# Inicializa el Dobot (la clase 'magician' se crea automáticamente al importar)
magician.set_home()
magician.clear_alarm()

print("Esperando red neuronal...")

while True:
    # === acá iría tu red neuronal ===
    # por ahora simulamos predicciones
    x = random.uniform(180, 260)
    y = random.uniform(-40, 40)
    z = random.uniform(0, 60)
    r = 0

    print(f"Moviendo a: x={x:.1f}, y={y:.1f}, z={z:.1f}, r={r}")

    magician.ptp(1, x, y, z, r)   # MOVJ cartesiano
    magician.wait(2)

    pose = magician.get_pose()
    print("Pose actual:", pose)
