import json
import time
from pathlib import Path
from datetime import datetime

import cv2

from lib.dobot_utils import detectar_puerto, move_to_xyzr, suck


H_JSON = Path("JSON/Matriz_H.json")

# === CONFIG CAMARA ===
CAM_INDEX = 0              # 0 suele ser la USB principal; si no, probá 1,2...
# CAM_W = 1280               # ejemplo: 1280
# CAM_H = 720                # ejemplo: 720
CAM_FPS = 30                # opcional
SHOW_PREVIEW = False        # SSH/headless: NO usar imshow


# === DATASET ===
# OUT_DIR = Path("dataset_raw")
SHOW_PREVIEW = True        # muestra ventana con la imagen
JPEG_QUALITY = 95          # 0-100


def load_vision_pose(json_path: Path) -> dict:
    """
    Lee vision pose del JSON.
    Soporta varios formatos razonables.
    Espera x,y,z,r en mm/grados (según tu wrapper).
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # formatos posibles
    pose = None
    for key in ["vision_pose", "visionPose", "vision", "pose_vision"]:
        if key in data:
            pose = data[key]
            break

    # si no está directo, probar anidado
    if pose is None and "calibration" in data:
        for key in ["vision_pose", "visionPose", "vision"]:
            if key in data["calibration"]:
                pose = data["calibration"][key]
                break

    if pose is None:
        raise KeyError(
            "No encontré vision_pose en el JSON. "
            "Busqué: vision_pose/visionPose/vision/pose_vision."
        )

    # normalizar nombres
    x = pose.get("x")
    y = pose.get("y")
    z = pose.get("z")
    r = pose.get("r", 0)

    if any(v is None for v in [x, y, z]):
        raise ValueError(f"vision_pose incompleto: {pose}")

    return {"x": float(x), "y": float(y), "z": float(z), "r": float(r)}


def load_camera_config(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    cam = data.get("camera", {})
    res = cam.get("resolution", [1280, 720])
    return int(res[0]), int(res[1])


def open_camera(index: int, w: int, h: int, fps: int | None = None) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        raise RuntimeError(
            f"No pude abrir la cámara (index={index}). "
            "Probá con CAM_INDEX=1 o 2."
        )

    # pedir resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  float(w))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(h))
    if fps is not None:
        cap.set(cv2.CAP_PROP_FPS, float(fps))

    # leer resolución real obtenida
    real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    real_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"📷 Cámara abierta: {real_w}x{real_h} @ {real_fps:.1f} fps (pedido: {w}x{h})")

    return cap


def save_frame(frame, out_dir: Path, quality: int = 95) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(out_dir.glob("img_*.jpg"))
    idx = len(existing) + 1
    path = out_dir / f"img_{idx:04d}.jpg"

    ok = cv2.imwrite(
        str(path),
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    if not ok:
        raise RuntimeError("cv2.imwrite falló guardando la imagen")

    return path


def main():
    # === pedir nombre de clase ===
    class_name = input("🧠 Ingresá el nombre de la clase: ").strip()

    if not class_name:
        raise ValueError("El nombre de la clase no puede estar vacío")

    DATASET_ROOT = Path("dataset")
    OUT_DIR = DATASET_ROOT / class_name

    # === 1) Conectar Dobot ===
    from pydobot import Dobot  # import local para no molestar si no está instalado

    port = detectar_puerto()
    device = Dobot(port=port, verbose=False)
    print(f"✅ Dobot conectado en {port}")

    # === 2) Cargar vision_pose del JSON ===
    vision_pose = load_vision_pose(H_JSON)
    print(f"🎯 Vision pose: {vision_pose}")

    # === 3) Mover a vision pose y apagar succión ===
    # suck(device, False)
    move_to_xyzr(device, vision_pose["x"], vision_pose["y"], vision_pose["z"], vision_pose["r"])
    print("🤖 Robot en vision_pose. Queda quieto para capturar dataset.")

    # === 4) Abrir cámara con resolución deseada ===
    # === cargar resolucion desde JSON ===
    cam_w, cam_h = load_camera_config(H_JSON)
    print(f"📷 Resolución pedida desde JSON: {cam_w}x{cam_h}")

    cap = open_camera(
        CAM_INDEX,
        cam_w,
        cam_h,
        fps=CAM_FPS
    )

    # “Warm-up” para autoexposición
    for _ in range(10):
        cap.read()
        time.sleep(0.03)

    print("\nControles (SSH/headless):")
    print("  Enter  -> guardar imagen")
    print("  q      -> salir")

    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "q":
                break

            # Capturar un frame (podés leer 2-3 para estabilizar autoexposición)
            frame = None
            for _ in range(3):
                ret, fr = cap.read()
                if ret:
                    frame = fr

            if frame is None:
                print("⚠️ No pude leer frame. Reintentando...")
                continue

            path = save_frame(frame, OUT_DIR, quality=JPEG_QUALITY)
            print(f"💾 Guardada: {path}")

    except KeyboardInterrupt:
        print("\n🛑 Cortado por usuario.")

    finally:
        cap.release()
        print("✅ Cámara cerrada.")



if __name__ == "__main__":
    main()
