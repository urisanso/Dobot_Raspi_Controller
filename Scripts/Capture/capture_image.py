import cv2

for i in range(0, 32):
    cap = cv2.VideoCapture(i)
    ret, frame = cap.read()
    if ret:
        print(f"✅ Cámara funcional encontrada en /dev/video{i}")
        cv2.imwrite(f"test_cam_{i}.jpg", frame)
        print(f"   → Imagen guardada como test_cam_{i}.jpg")
        cap.release()
        break
    cap.release()
else:
    print("⚠️ Ninguna cámara devolvió imagen válida")