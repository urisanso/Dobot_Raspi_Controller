# 🦾 Control del Dobot Magician desde Raspberry Pi

Proyecto para controlar el **Dobot Magician (modelo común, no Lite)** directamente desde una **Raspberry Pi**, sin PC intermedia ni DobotLink.  
Incluye scripts de homing, control cartesiano, control articular y modo manual por teclado.

---

## ⚙️ Instalación del entorno

```bash
sudo apt update
sudo apt install python3-pip python3-venv libatlas-base-dev
python3 -m venv venv
source venv/bin/activate
pip install pydobot
```

> ⚠️ Asegurate de estar en la Raspberry Pi OS 64 bits (`aarch64`)  
> y de tener `numpy` funcionando (`python -c "import numpy; print(numpy.__version__)"`).

---

## 🔌 Conexión

1. Conectá el Dobot por **USB**.  
2. Verificá el puerto asignado:
   ```bash
   ls /dev/tty*
   ```
   Normalmente será `/dev/ttyACM0` o `/dev/ttyUSB0`.

3. Agregá tu usuario al grupo `dialout`:
   ```bash
   sudo usermod -aG dialout $USER
   ```
   Cerrá sesión y volvé a entrar.

---

## 🧠 1. Movimiento cartesiano básico

Archivo: `dobot_cartesian_demo.py`

```python
from pydobot import Dobot
import serial.tools.list_ports, time

port = [p.device for p in serial.tools.list_ports.comports()
        if 'USB' in p.description or 'ACM' in p.device][0]
device = Dobot(port=port)

print("Posición inicial:", device.pose())

device.speed(50)
device.move_to(250, 0, 50, 0)
time.sleep(2)
device.move_to(200, 100, 30, 0)
time.sleep(2)
device.move_to(250, 0, 50, 0)

device.suck(True)
time.sleep(1)
device.suck(False)

print("Posición final:", device.pose())
device.close()
```

---

## 🦿 2. Movimiento articular (Joint)

Archivo: `dobot_joints_demo.py`

```python
from pydobot import Dobot, enums
import serial.tools.list_ports, time

port = [p.device for p in serial.tools.list_ports.comports()
        if 'USB' in p.description or 'ACM' in p.device][0]
device = Dobot(port=port)

# Movimiento por articulaciones (modo 4 = MOVJ_ANGLE)
device._set_ptp_cmd(x=0, y=30, z=-20, r=10,
                    mode=enums.PTPMode.MOVJ_ANGLE, wait=True)
time.sleep(2)
device._set_ptp_cmd(x=0, y=0, z=0, r=0,
                    mode=enums.PTPMode.MOVJ_ANGLE, wait=True)
device.close()
```

---

## 🎮 3. Control manual por teclado (modo Jog)

Archivo: `dobot_jog_joints.py`

Controla las 4 juntas usando `curses` (no GUI, ideal para terminal SSH).

| Joint | Teclas | Movimiento |
|:------|:-------|:------------|
| J1 | Q / A | + / – |
| J2 | W / S | + / – |
| J3 | E / D | + / – |
| J4 | R / F | + / – |
| Reset | Z | vuelve a 0 |
| Salir | X | finaliza programa |

```bash
python dobot_jog_joints.py
```

---

## 🧩 4. Modos PTP disponibles

Listados automáticamente desde `pydobot.enums.PTPMode`:

| Valor | Modo | Descripción |
|:------|:------|:-------------|
| 0 | `JUMP_XYZ` | Salto cartesiano |
| 1 | `MOVJ_XYZ` | PTP joint a posición cartesiana |
| 2 | `MOVL_XYZ` | Trayectoria lineal recta |
| 3 | `JUMP_ANGLE` | Salto en ángulos articulares |
| 4 | `MOVJ_ANGLE` | Movimiento articular (**modo joint**) |
| 5 | `MOVL_ANGLE` | Lineal articular |
| 6 | `MOVJ_INC` | Incremental por juntas |
| 7 | `MOVL_INC` | Incremental cartesiano |
| 8 | `MOVJ_XYZ_INC` | Incremental cartesiano (joint interp.) |
| 9 | `JUMP_MOVL_XYZ` | Combinado salto + lineal |

---

## 🧾 5. Próximos pasos

- [ ] Agregar feedback real de posición con `pose()`  
- [ ] Implementar grabado de trayectorias (`JSON` o CSV)  
- [ ] Integrar modelo de visión o red neuronal (detección → coordenadas → movimiento)

---

## 👨‍🔧 Créditos

Scripts y documentación adaptados para Raspberry Pi + Dobot Magician (modelo común) usando la librería `pydobot`.  
Versión verificada: Python 3.11 / pydobot 1.3.x / ARM 64 (aarch64)
