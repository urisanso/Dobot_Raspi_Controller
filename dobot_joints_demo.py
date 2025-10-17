from pydobot import Dobot, enums
import serial.tools.list_ports, time

port = [p.device for p in serial.tools.list_ports.comports() if 'USB' in p.description or 'ACM' in p.device][0]
device = Dobot(port=port)

# Ejemplo: mover por articulaciones (modo 4)
device._set_ptp_cmd(
    x=0, y=30, z=-20, r=10,
    mode=enums.PTPMode.MOVJ_ANGLE,  # <— movimiento por juntas
    wait=True
)

time.sleep(2)

# Volver al origen
device._set_ptp_cmd(
    x=0, y=0, z=0, r=0,
    mode=enums.PTPMode.MOVJ_ANGLE,
    wait=True
)

device.close()
