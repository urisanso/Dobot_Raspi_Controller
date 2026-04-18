import glob
from datetime import date
from pathlib import Path

# ── NUEVO: gestión de archivo de inventario ──────────────────────────────────

def buscar_ultimo_inventario():
    """Devuelve el archivo inventario_*.txt más reciente, o None si no hay ninguno."""
    archivos = sorted(glob.glob("inventario_*.txt"), reverse=True)
    return archivos[0] if archivos else None

def nuevo_nombre_inventario():
    """Genera un nombre con la fecha de hoy y pide el nro. de kit al usuario."""
    hoy = date.today().strftime("%Y-%m-%d")
    while True:
        nro = input("  → Número de kit: ").strip()
        if nro:
            return f"inventario_{hoy}_kit{nro}.txt"
        print("  El número de kit no puede estar vacío.")

def seleccionar_inventario():
    """
    Al arrancar, pregunta si se quiere continuar con el último inventario
    o empezar uno nuevo. Devuelve el path del archivo a usar.
    """
    print("\n" + "="*50)
    print("  GESTIÓN DE INVENTARIO")
    print("="*50)

    ultimo = buscar_ultimo_inventario()

    if ultimo:
        print(f"\n  Último inventario encontrado: {ultimo}")
        while True:
            resp = input("  ¿Continuar con este archivo? [s/n]: ").strip().lower()
            if resp == "s":
                print(f"  ✅ Continuando con: {ultimo}")
                return ultimo
            elif resp == "n":
                nombre = nuevo_nombre_inventario()
                print(f"  ✅ Nuevo inventario: {nombre}")
                return nombre
            else:
                print("  Ingresá 's' o 'n'.")
    else:
        print("\n  No se encontraron inventarios previos.")
        nombre = nuevo_nombre_inventario()
        print(f"  ✅ Nuevo inventario: {nombre}")
        return nombre

# ── Modificación de actualizar_inventario ───────────────────────────────────

def actualizar_inventario(clase_detectada, archivo_path):
    """Ahora recibe el path del archivo en lugar de usar uno fijo."""
    inventario = {}

    if Path(archivo_path).exists():
        with open(archivo_path, "r") as f:
            for linea in f:
                if ":" in linea:
                    nombre, cantidad = linea.split(":", 1)
                    inventario[nombre.strip()] = int(cantidad.strip())

    inventario[clase_detectada] = inventario.get(clase_detectada, 0) + 1

    with open(archivo_path, "w") as f:
        for nombre, cantidad in inventario.items():
            f.write(f"{nombre}: {cantidad}\n")

    print(f"📊 Inventario actualizado: {clase_detectada} → {inventario[clase_detectada]} | archivo: {archivo_path}")