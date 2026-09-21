import cv2
import os

VIDEO_PATH = "input.mp4"
OUTPUT_DIR = "outputs/frames"
EVERY_N_FRAMES = 60

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_PATH)

frame_number = 0
saved = 0

while True:
    success, frame = cap.read()

    if not success:
        break

    if frame_number % EVERY_N_FRAMES == 0:
        path = f"{OUTPUT_DIR}/frame_{saved:05d}.jpg"
        cv2.imwrite(path, frame)
        saved += 1

    frame_number += 1

cap.release()

print(f"Saved {saved} frames")