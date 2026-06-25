"""
Shared swing-metric extractor.

Runs MediaPipe Pose over a video, draws a skeleton + key angle overlays,
writes an annotated MP4, and returns a dict of summary metrics that can be
used for side-by-side swing comparison.
"""

import math
import subprocess
from pathlib import Path

import cv2
import mediapipe as mp


def _angle(a, b, c):
    """Interior angle (degrees) at point b formed by a-b-c."""
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0])
        - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle


def _line_angle(p1, p2):
    """Angle (degrees) of the line p1->p2 relative to horizontal."""
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def _norm(angle):
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def extract_swing_metrics(input_path, output_path):
    """
    Process a single video.

    Returns a dict:
        {
          "frames": int,
          "tracked_frames": int,
          "max_x_factor": float,
          "avg_x_factor": float,
          "min_elbow_angle": float,      # deepest elbow bend
          "min_knee_angle": float,       # deepest knee flex
          "max_shoulder_turn": float,
          "max_hip_turn": float
        }
    or None if the video could not be opened.
    """
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        pose.close()
        return None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    temp_output = str(output_path).replace(".mp4", "_temp.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    x_factors = []
    elbow_angles = []
    knee_angles = []
    shoulder_turns = []
    hip_turns = []

    total_frames = 0
    tracked_frames = 0

    while True:
        success, frame = cap.read()
        if not success:
            break
        total_frames += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = pose.process(rgb)
        rgb.flags.writeable = True

        if results.pose_landmarks:
            tracked_frames += 1

            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
            )

            lm = results.pose_landmarks.landmark

            def pt(landmark):
                return (int(landmark.x * width), int(landmark.y * height))

            l_sh = pt(lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
            r_sh = pt(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])
            l_hip = pt(lm[mp_pose.PoseLandmark.LEFT_HIP])
            r_hip = pt(lm[mp_pose.PoseLandmark.RIGHT_HIP])
            r_elbow = pt(lm[mp_pose.PoseLandmark.RIGHT_ELBOW])
            r_wrist = pt(lm[mp_pose.PoseLandmark.RIGHT_WRIST])
            r_knee = pt(lm[mp_pose.PoseLandmark.RIGHT_KNEE])
            r_ankle = pt(lm[mp_pose.PoseLandmark.RIGHT_ANKLE])

            # X-Factor: shoulder line vs hip line separation
            shoulder_angle = _line_angle(l_sh, r_sh)
            hip_angle = _line_angle(l_hip, r_hip)
            x_factor = _norm(shoulder_angle - hip_angle)
            x_factors.append(x_factor)

            shoulder_turns.append(_norm(shoulder_angle))
            hip_turns.append(_norm(hip_angle))

            # Elbow + knee angles (right side)
            elbow_angle = _angle(r_sh, r_elbow, r_wrist)
            knee_angle = _angle(r_hip, r_knee, r_ankle)
            elbow_angles.append(elbow_angle)
            knee_angles.append(knee_angle)

            # Overlays
            cv2.line(frame, l_sh, r_sh, (0, 255, 255), 4)
            cv2.line(frame, l_hip, r_hip, (255, 255, 255), 4)
            cv2.putText(frame, f"X:{int(x_factor)}", (r_sh[0] + 20, r_sh[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"E:{int(elbow_angle)}", (r_elbow[0] + 20, r_elbow[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"K:{int(knee_angle)}", (r_knee[0] + 20, r_knee[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        out.write(frame)

    cap.release()
    out.release()
    pose.close()

    # Re-encode to browser-friendly H.264
    subprocess.run(
        ["ffmpeg", "-y", "-i", temp_output, "-vcodec", "libx264",
         "-pix_fmt", "yuv420p", str(output_path)],
        check=False,
    )
    Path(temp_output).unlink(missing_ok=True)

    if tracked_frames == 0:
        return {
            "frames": total_frames,
            "tracked_frames": 0,
            "max_x_factor": 0.0,
            "avg_x_factor": 0.0,
            "min_elbow_angle": 0.0,
            "min_knee_angle": 0.0,
            "max_shoulder_turn": 0.0,
            "max_hip_turn": 0.0,
        }

    return {
        "frames": total_frames,
        "tracked_frames": tracked_frames,
        "max_x_factor": round(max(x_factors), 1),
        "avg_x_factor": round(_mean(x_factors), 1),
        "min_elbow_angle": round(min(elbow_angles), 1),
        "min_knee_angle": round(min(knee_angles), 1),
        "max_shoulder_turn": round(max(shoulder_turns), 1),
        "max_hip_turn": round(max(hip_turns), 1),
    }
