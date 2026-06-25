import cv2
import mediapipe as mp
import math
import subprocess
from pathlib import Path


def calculate_line_angle(point1, point2):

    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]

    angle = math.degrees(math.atan2(dy, dx))

    return angle


def normalize_angle(angle):

    angle = abs(angle)

    if angle > 180:
        angle = 360 - angle

    return angle


def run_xfactor_analysis(input_path, output_path):

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

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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

            left_shoulder = landmarks[
                mp_pose.PoseLandmark.LEFT_SHOULDER
            ]

            right_shoulder = landmarks[
                mp_pose.PoseLandmark.RIGHT_SHOULDER
            ]

            left_hip = landmarks[
                mp_pose.PoseLandmark.LEFT_HIP
            ]

            right_hip = landmarks[
                mp_pose.PoseLandmark.RIGHT_HIP
            ]

            left_shoulder_point = (
                int(left_shoulder.x * width),
                int(left_shoulder.y * height)
            )

            right_shoulder_point = (
                int(right_shoulder.x * width),
                int(right_shoulder.y * height)
            )

            left_hip_point = (
                int(left_hip.x * width),
                int(left_hip.y * height)
            )

            right_hip_point = (
                int(right_hip.x * width),
                int(right_hip.y * height)
            )

            shoulder_angle = calculate_line_angle(
                left_shoulder_point,
                right_shoulder_point
            )

            hip_angle = calculate_line_angle(
                left_hip_point,
                right_hip_point
            )

            x_factor = normalize_angle(
                shoulder_angle - hip_angle
            )

            cv2.line(
                frame,
                left_shoulder_point,
                right_shoulder_point,
                (0, 255, 255),
                5
            )

            cv2.line(
                frame,
                left_hip_point,
                right_hip_point,
                (255, 255, 255),
                5
            )

            shoulder_midpoint = (
                int((left_shoulder_point[0] + right_shoulder_point[0]) / 2),
                int((left_shoulder_point[1] + right_shoulder_point[1]) / 2)
            )

            hip_midpoint = (
                int((left_hip_point[0] + right_hip_point[0]) / 2),
                int((left_hip_point[1] + right_hip_point[1]) / 2)
            )

            torso_center = (
                int((shoulder_midpoint[0] + hip_midpoint[0]) / 2),
                int((shoulder_midpoint[1] + hip_midpoint[1]) / 2)
            )

            cv2.putText(
                frame,
                f"S: {int(shoulder_angle)}",
                (
                    shoulder_midpoint[0] + 40,
                    shoulder_midpoint[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"H: {int(hip_angle)}",
                (
                    hip_midpoint[0] + 40,
                    hip_midpoint[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"X: {int(x_factor)}",
                (
                    torso_center[0] + 50,
                    torso_center[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                3
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