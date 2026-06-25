import cv2
import mediapipe as mp
import subprocess
from pathlib import Path
import math


def run_hipturn_analysis(input_path, output_path):

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(str(input_path))

    if not cap.isOpened():
        raise Exception("Could not open input video")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    temp_output = str(output_path).replace(".mp4", "_temp.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    while True:
        success, frame = cap.read()

        if not success:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            left_hip = landmarks[23]
            right_hip = landmarks[24]

            lx, ly = int(left_hip.x * width), int(left_hip.y * height)
            rx, ry = int(right_hip.x * width), int(right_hip.y * height)

            dx = rx - lx
            dy = ry - ly

            hip_angle = math.degrees(math.atan2(dy, dx))

            text_x = int((lx + rx) / 2)
            text_y = int((ly + ry) / 2) - 15

            cv2.line(frame, (lx, ly), (rx, ry), (255, 255, 255), 4)

            cv2.circle(frame, (lx, ly), 8, (255, 255, 255), -1)
            cv2.circle(frame, (rx, ry), 8, (255, 255, 255), -1)

            cv2.putText(
                frame,
                f"{hip_angle:.1f} deg",
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        out.write(frame)

    cap.release()
    out.release()
    pose.close()

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", temp_output,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ])

    Path(temp_output).unlink(missing_ok=True)

    return output_path