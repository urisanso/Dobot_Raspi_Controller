import numpy as np
import cv2

def pixel_to_robot(u, v, H):
    p = np.array([u, v, 1.0], dtype=np.float32)
    r = H @ p
    r /= r[2]
    return r[0], r[1]

pixel_points = [
    (214, 465),
    (207, 289),
    (200, 110),

    (449, 462),
    (444, 287),
    (437, 108),

    (680, 459),
    (676, 285),
    (672, 106),

    (911, 457),
    (909, 282),
    (907, 103),

    (1139, 455),
    (1139, 281),
    (1141, 101)
]


dx = 25
dy = 40 * 14 / 17  # 32.941176...

robot_points = [
    (294.0,  87.50),
    (319.0,  87.50),
    (344.0,  87.50),

    (294.0,  54.56),
    (319.0,  54.56),
    (344.0,  54.56),

    (294.0,  21.62),
    (319.0,  21.62),
    (344.0,  21.62),

    (294.0, -11.32),
    (319.0, -11.32),
    (344.0, -11.32),

    (294.0, -44.26),
    (319.0, -44.26),
    (344.0, -44.26)
]



pixel_points = np.array(pixel_points, dtype=np.float32)
robot_points = np.array(robot_points, dtype=np.float32)

H1, mask = cv2.findHomography(
    pixel_points,
    robot_points,
    method=cv2.RANSAC,
    ransacReprojThreshold=3.0
)

print("Homografía H1:")
print(H1)

inliers1 = mask.ravel().sum()
print(f"Puntos usados: {inliers1} / {len(pixel_points)}")


A, inliers2 = cv2.estimateAffine2D(
    pixel_points,
    robot_points,
    method=cv2.RANSAC,
    ransacReprojThreshold=2.0
)

print("Matriz afín A (2x3):")
print(A)

print(f"Inliers: {int(inliers2.sum())} / {len(pixel_points)}")

# Pasamos a 3x3
H2 = np.vstack([A, [0, 0, 1]])

print("\nMatriz H2 final (3x3):")
print(H2)

H3 = H1
H3[2,0] = 0.0
H3[2,1] = 0.0
H3[2,2] = 1.0

print(H3)

# ejemplo de test
u_test, v_test = 1139, 455
xr1, yr1 = pixel_to_robot(u_test, v_test, H1)
xr2, yr2 = pixel_to_robot(u_test, v_test, H3)
print(f"con H1 - Pixel ({u_test},{v_test}) → Robot ({xr1:.2f}, {yr1:.2f})")
print(f"con H2 - Pixel ({u_test},{v_test}) → Robot ({xr2:.2f}, {yr2:.2f})")
xr = (xr1+xr2)/2
yr = (yr1+yr2)/2
print(f"Promedio - Pixel ({u_test},{v_test}) → Robot ({xr:.2f}, {yr:.2f})")
