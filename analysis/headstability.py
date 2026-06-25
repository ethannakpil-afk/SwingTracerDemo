import cv2
import mediapipe as mp
import math
import subprocess
from pathlib import Path


def calculate_distance(point1, point2):

    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]

    distance = math.sqrt(dx ** 2 + dy ** 2)

    return distance


def run_headstability_analysis(input_path, output_path):

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

    head_path = []
    starting_head_point = None

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

            nose = landmarks[mp_pose.PoseLandmark.NOSE]

            head_point = (
                int(nose.x * width),
                int(nose.y * height)
            )

            if starting_head_point is None:
                starting_head_point = head_point

            head_path.append(head_point)

            head_movement = calculate_distance(
                starting_head_point,
                head_point
            )

            cv2.circle(
                frame,
                starting_head_point,
                12,
                (255, 255, 255),
                2
            )

            cv2.circle(
                frame,
                head_point,
                10,
                (0, 255, 255),
                -1
            )

            cv2.line(
                frame,
                starting_head_point,
                head_point,
                (0, 255, 255),
                3
            )

            for i in range(1, len(head_path)):
                cv2.line(
                    frame,
                    head_path[i - 1],
                    head_path[i],
                    (0, 255, 255),
                    3
                )

            cv2.putText(
                frame,
                f"Head Move: {int(head_movement)} px",
                (
                    head_point[0] + 40,
                    head_point[1]
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