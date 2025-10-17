# dobot_utils.py
#!/usr/bin/env python3 
import time, json
from pydobot import enums

# ==================== FUNCIONES DE MOVIMIENTO ====================

def home_fisico(device):
    """
    Realiza el homing físico real del Dobot.
    (Simula el G28 pero con la API de pydobot)
    """
    try:
        print("🏠 Ejecutando HOME físico...")
        device._set_queued_cmd_clear()
        device._set_ptp_cmd(
            x=200, y=0, z=50, r=0,
            mode=enums.PTPMode.MOVJ_XYZ, wait=True
        )
        print("✅ Home físico completado.")
    except Exception as e:
        print(f"⚠️ Error en home físico: {e}")


def home_logico(device, puntos):
    """
    Va al punto guardado 'P_HOME' si existe.
    """
    if "P_HOME" not in puntos:
        print("⚠️ No hay punto 'P_HOME' guardado.")
        return
    x, y, z, r = puntos["P_HOME"]
    move_to_xyzr(device, x, y, z, r, wait=True)
    print("✅ Home lógico completado.")


def move_to_xyzr(device, x, y, z, r, wait=True):
    """
    Movimiento cartesiano a coordenadas (x, y, z, r).
    """
    try:
        device.move_to(x, y, z, r, wait=wait)
    except Exception as e:
        print(f"⚠️ Error moviendo XYZR: {e}")


def move_joints(device, j1, j2, j3, j4, wait=True):
    """
    Movimiento por juntas (modo 4 = MOVJ_ANGLE)
    """
    try:
        device._set_ptp_cmd(
            x=j1, y=j2, z=j3, r=j4,
            mode=enums.PTPMode.MOVJ_ANGLE,
            wait=wait
        )
    except Exception as e:
        print(f"⚠️ Error moviendo joints: {e}")


def suck(device, state: bool):
    """
    Activa o desactiva la bomba de vacío.
    """
    try:
        device._set_end_effector_suction_cup(enable=state, on=True)
        print(f"✅ Bomba {'ON' if state else 'OFF'}.")
    except Exception as e:
        print(f"⚠️ Error bomba: {e}")


def clear_alarm(device):
    """
    Limpia alarmas internas y cola de comandos.
    """
    try:
        device._set_queued_cmd_clear()
        device._set_queued_cmd_start_exec()
        print("✅ Alarmas y cola limpiadas.")
    except Exception as e:
        print(f"⚠️ Error clear alarm: {e}")

# ==================== FUNCIONES DE PERSISTENCIA ====================

def save_points(puntos, filename="puntos.json"):
    try:
        with open(filename, "w") as f:
            json.dump(puntos, f, indent=4)
        print("💾 Puntos guardados.")
    except Exception as e:
        print(f"⚠️ Error guardando puntos: {e}")

def load_points(filename="puntos.json"):
    try:
        with open(filename, "r") as f:
            txt = f.read().strip()
            return json.loads(txt) if txt else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
