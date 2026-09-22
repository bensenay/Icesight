import cv2
import os

VIDEO_PATH = "data/raw/goal1.mp4"
OUTPUT_DIR = "data/frames"

SECONDS_BETWEEN_FRAMES = 0.1

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_PATH)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps * SECONDS_BETWEEN_FRAMES)

frame_number = 0
saved = 0

while True:
    success, frame = cap.read()

    if not success:
        break

    if frame_number % frame_interval == 0:
        path = os.path.join(
            OUTPUT_DIR,
            f"frame_{saved:05d}.jpg"
        )

        cv2.imwrite(path, frame)
        saved += 1

    frame_number += 1

cap.release()

print(f"Saved {saved} frames")