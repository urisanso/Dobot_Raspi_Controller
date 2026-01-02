# dobot_utils.py
#!/usr/bin/env python3
import time, json
import os, csv
from datetime import datetime
from pydobot import enums

# ==================== FUNCIONES DE MOVIMIENTO ====================

def home_fisico(device):
    """Ejecuta el homing físico real (equivalente a G28)."""
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
    """Va al punto guardado 'P_HOME' si existe."""
    if "P_HOME" not in puntos:
        print("⚠️ No hay punto 'P_HOME' guardado.")
        return
    x, y, z, r = puntos["P_HOME"]
    move_to_xyzr(device, x, y, z, r, wait=True)
    print("✅ Home lógico completado.")


def move_to_xyzr(device, x, y, z, r, wait=True):
    """Movimiento cartesiano a coordenadas (x, y, z, r)."""
    try:
        device.move_to(x, y, z, r, wait=wait)
    except Exception as e:
        print(f"⚠️ Error moviendo XYZR: {e}")


def move_joints(device, j1, j2, j3, j4, wait=False):
    """Movimiento por juntas (MOVJ_ANGLE)."""
    try:
        device._set_ptp_cmd(
            x=j1, y=j2, z=j3, r=j4,
            mode=enums.PTPMode.MOVJ_ANGLE,
            wait=wait
        )
    except Exception as e:
        print(f"⚠️ Error moviendo joints: {e}")


# -----------------------------------------------------
# CONTROL DE BOMBA (vacío / soplado)
# -----------------------------------------------------
INVERTIR_BOMBA = True  # ← cambiá a False si querés volver al sentido original

def suck(device, state: bool):
    """Activa o desactiva la bomba de vacío (con opción de invertir polaridad)."""
    try:
        # Si INVERTIR_BOMBA=True, el estado se invierte lógicamente
        state_real = not state if INVERTIR_BOMBA else state
        device._set_end_effector_suction_cup(enable=state_real) #, on=True
        print(f"✅ Bomba {'ON (vacío)' if state else 'OFF (liberando)'}")
    except Exception as e:
        print(f"⚠️ Error control bomba: {e}")

def gripper(device, state: bool):
    """
    Alias de suck() para compatibilidad.
    True  -> cerrar (vacío)
    False -> abrir (aire)
    """
    suck(device, state)



def clear_alarm(device):
    """Limpia alarmas internas y cola de comandos."""
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

# =====================================================
# NUEVAS FUNCIONES PARA REGISTRO Y REPRODUCCIÓN
# =====================================================

def detectar_puerto():
    """Detecta automáticamente el puerto del Dobot conectado por USB."""
    import serial.tools.list_ports
    for p in serial.tools.list_ports.comports():
        if "USB" in p.device or "ACM" in p.device:
            return p.device
    return None

def crear_archivo_trayectoria(dir_salida="data/trayectorias"):
    """Crea un nuevo archivo CSV en la carpeta indicada y devuelve su path."""
    if not os.path.exists(dir_salida):
        os.makedirs(dir_salida)
    nombre = f"trayectoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(dir_salida, nombre)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "J1", "J2", "J3", "J4"])
    return path

def append_trayectoria(path, j1, j2, j3, j4, punto=None, bomba=0):
    """Agrega un punto articular (J1–J4) con timestamp, nombre y estado de bomba."""
    import csv, time
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            time.time(),
            f"{j1:.3f}", f"{j2:.3f}", f"{j3:.3f}", f"{j4:.3f}",
            punto or "", bomba
        ])

def reproducir_trayectoria(device, path):
    """Ejecuta la trayectoria grabada desde un CSV, incluyendo la bomba."""
    import csv, os, time
    from pydobot import enums
    if not os.path.exists(path):
        print("⚠️ No hay archivo para reproducir.")
        return
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # encabezado
        for row in reader:
            j1, j2, j3, j4 = map(float, row[1:5])
            bomba = int(row[6]) if len(row) > 6 else 0
            # Actualizar bomba si es necesario
            if bomba:
                device.suck(True)
            else:
                device.suck(False)
            # Mover a posición
            device._set_ptp_cmd(
                x=j1, y=j2, z=j3, r=j4,
                mode=enums.PTPMode.MOVJ_ANGLE,
                wait=True
            )
    print("✅ Reproducción completada.")
