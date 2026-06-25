import cv2
import mediapipe as mp
import math
import subprocess
from pathlib import Path


def calculate_spine_angle(shoulder, hip):

    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]

    angle = math.degrees(
        math.atan2(abs(dx), abs(dy))
    )

    return angle


def run_posture_analysis(input_path, output_path):

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

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

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = pose.process(rgb_frame)

        if results.pose_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(
                    color=(0, 255, 0),
                    thickness=3,
                    circle_radius=3
                ),
                mp_drawing.DrawingSpec(
                    color=(255, 0, 0),
                    thickness=2,
                    circle_radius=2
                )
            )

            landmarks = results.pose_landmarks.landmark

            right_shoulder = landmarks[
                mp_pose.PoseLandmark.RIGHT_SHOULDER
            ]

            right_hip = landmarks[
                mp_pose.PoseLandmark.RIGHT_HIP
            ]

            shoulder = (
                int(right_shoulder.x * width),
                int(right_shoulder.y * height)
            )

            hip = (
                int(right_hip.x * width),
                int(right_hip.y * height)
            )

            spine_angle = calculate_spine_angle(
                shoulder,
                hip
            )

            cv2.line(
                frame,
                shoulder,
                hip,
                (0, 255, 255),
                4
            )

            vertical_point = (
                hip[0],
                hip[1] - 150
            )

            cv2.line(
                frame,
                hip,
                vertical_point,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Posture: {int(spine_angle)}",
                (
                    hip[0] + 40,
                    hip[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
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