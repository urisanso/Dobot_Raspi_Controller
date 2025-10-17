# dobot_utils.py 
import time, json

def home(device):
    """HOME real (G28)."""
    try:
        device.ser.write(b'G28\n')
        device.ser.flush()
        time.sleep(5)
        print("✅ Home ejecutado.")
    except Exception as e:
        print(f"⚠️ Error haciendo home: {e}")

def go_home(device, puntos):
    if "P_HOME" not in puntos:
        print("⚠️ No hay punto HOME guardado.")
        return
    x, y, z, r = puntos["P_HOME"]
    move_to_xyzr(device, x, y, z, r, wait=True)

def suck(device, state: bool):
    try:
        cmd = b'M2231 V1\n' if state else b'M2231 V0\n'
        device.ser.write(cmd); device.ser.flush()
        print(f"✅ Bomba {'ON' if state else 'OFF'}.")
    except Exception as e:
        print(f"⚠️ Error bomba: {e}")

def move_to_xyzr(device, x, y, z, r, wait=True):
    try:
        device.move_to(x, y, z, r, wait=wait)
    except Exception as e:
        print(f"⚠️ Error moviendo XYZR: {e}")

def move_joints(device, j1, j2, j3, j4, speed=5000):
    """Movimiento articular real (G220)."""
    try:
        gcode = f'G220 J1 {j1:.3f} J2 {j2:.3f} J3 {j3:.3f} J4 {j4:.3f} F{speed}\n'
        device.ser.write(gcode.encode()); device.ser.flush()
    except Exception as e:
        print(f"⚠️ Error moviendo joints: {e}")

def save_points(puntos, filename="puntos.json"):
    with open(filename, "w") as f:
        json.dump(puntos, f, indent=4)
    print("💾 Puntos guardados.")

def load_points(filename="puntos.json"):
    try:
        with open(filename, "r") as f:
            txt = f.read().strip()
            return json.loads(txt) if txt else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def clear_alarm(device):
    """Limpia alarmas reales (M2 + M17)."""
    try:
        device.ser.write(b'M2\n');  time.sleep(0.2)
        device.ser.write(b'M17\n'); device.ser.flush()
        print("✅ Alarma limpiada.")
    except Exception as e:
        print(f"⚠️ Error clear alarm: {e}")
