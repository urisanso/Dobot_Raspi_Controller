import json
import numpy as np
from pathlib import Path


def load_homography(json_path):
    """
    Carga la matriz H y la pose de visión desde un archivo JSON.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    H = np.array(data["pixel_to_robot"]["H"], dtype=float)
    vision_pose = data["vision_pose"]

    return H, vision_pose

def pixel_to_robot(u, v, H):
    """
    Aplica homografía para convertir (u, v) de imagen a (x, y) del robot.
    """
    p_img = np.array([u, v, 1.0])
    p_robot = H @ p_img
    p_robot /= p_robot[2]

    return float(p_robot[0]), float(p_robot[1])

def get_bbox_centers(detections, min_conf=0.6, ignore_classes=None):
    """
    Devuelve los centros de bounding boxes filtrados.
    """
    if ignore_classes is None:
        ignore_classes = []

    centers = []

    for p in detections:
        if p["confidence"] < min_conf:
            continue
        if p["class"] in ignore_classes:
            continue

        centers.append(
            {
                "class": p["class"],
                "confidence": p["confidence"],
                "x": p["x"],
                "y": p["y"],
                "width": p["width"],
                "height": p["height"],
            }
        )

    return centers
