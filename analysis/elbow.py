import cv2
import mediapipe as mp
import math
import subprocess

def calculate_angle(a, b, c):
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0])
        - math.atan2(a[1] - b[1], a[0] - b[0])
    )

    angle = abs(angle)

    if angle > 180:
        angle = 360 - angle

    return angle


def run_elbow_analysis(input_path, output_path):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(str(input_path))

    if not cap.isOpened():
        print("ERROR: Could not open video:", input_path)
        return None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 30



    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not out.isOpened():
        print("ERROR: Could not create output video:", output_path)
        cap.release()
        pose.close()
        return None

    while True:
        success, frame = cap.read()

        if not success:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = pose.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            landmarks = results.pose_landmarks.landmark
            frame_height, frame_width, _ = frame.shape

            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
            right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

            shoulder = (
                int(right_shoulder.x * frame_width),
                int(right_shoulder.y * frame_height)
            )

            elbow = (
                int(right_elbow.x * frame_width),
                int(right_elbow.y * frame_height)
            )

            wrist = (
                int(right_wrist.x * frame_width),
                int(right_wrist.y * frame_height)
            )

            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            cv2.line(frame, shoulder, elbow, (0, 255, 255), 5)
            cv2.line(frame, elbow, wrist, (0, 255, 255), 5)

            cv2.putText(
                frame,
                f"Elbow: {int(elbow_angle)}",
                (elbow[0] + 30, elbow[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )

        out.write(frame)


    cap.release()
    out.release()
    pose.close()

    temp_output = str(output_path).replace(".mp4", "_temp.mp4")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", str(output_path),
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        temp_output
    ])

    import os
    os.replace(temp_output, output_path)




    return output_path