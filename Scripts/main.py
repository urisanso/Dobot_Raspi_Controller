from vision import detect_objects, get_bbox_centers

API_KEY = "6CpctoE5C7mQOrwSaDWt"
PROJECT = "arcoiris-9o6ty"
VERSION = 2


def main():
    detections, frame = detect_objects(
        api_key=API_KEY,
        project=PROJECT,
        version=VERSION,
        save_debug=True,
    )

    targets = get_bbox_centers(
        detections,
        min_conf=0.8,
        ignore_classes=["vacio"],
    )

    if not targets:
        print("No hay objetos válidos")
        return

    target = targets[0]
    print("Objeto seleccionado:", target)

    # ACÁ VA LA SECUENCIA DEL DOBOT
    # move_robot_to_pixel(target["x"], target["y"])


if __name__ == "__main__":
    main()
