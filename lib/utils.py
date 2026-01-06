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
