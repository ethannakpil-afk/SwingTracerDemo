"""
Compare analytics.

Two modes:
  * compare_swing_videos(...) -> runs pose metrics on two videos and returns
    annotated output paths + a structured metric comparison.
  * compare_swing_csvs(...)   -> legacy CSV comparison (kept for compatibility).
"""

import pandas as pd

from analysis.swing_metrics import extract_swing_metrics


# Metric display config: key -> (label, unit, "higher"|"lower" is better-ish for context)
METRIC_FIELDS = [
    ("max_x_factor",     "Max X-Factor",      "deg"),
    ("avg_x_factor",     "Avg X-Factor",      "deg"),
    ("min_elbow_angle",  "Deepest Elbow Bend","deg"),
    ("min_knee_angle",   "Deepest Knee Flex", "deg"),
    ("max_shoulder_turn","Max Shoulder Turn", "deg"),
    ("max_hip_turn",     "Max Hip Turn",      "deg"),
    ("tracked_frames",   "Tracked Frames",    ""),
]


def compare_swing_videos(video1_path, output1_path, video2_path, output2_path):
    """
    Process both swing videos and build a comparison payload.

    Returns:
        {
          "swing_1": {metrics...},
          "swing_2": {metrics...},
          "metrics": [ {key,label,unit,swing_1,swing_2,difference}, ... ],
          "output_video_1": str(output1_path),
          "output_video_2": str(output2_path),
        }
    Raises ValueError if a video could not be processed.
    """
    metrics_1 = extract_swing_metrics(video1_path, output1_path)
    metrics_2 = extract_swing_metrics(video2_path, output2_path)

    if metrics_1 is None:
        raise ValueError("Could not process swing 1 video")
    if metrics_2 is None:
        raise ValueError("Could not process swing 2 video")

    rows = []
    for key, label, unit in METRIC_FIELDS:
        v1 = metrics_1.get(key, 0)
        v2 = metrics_2.get(key, 0)
        rows.append({
            "key": key,
            "label": label,
            "unit": unit,
            "swing_1": v1,
            "swing_2": v2,
            "difference": round(v2 - v1, 1),
        })

    return {
        "swing_1": metrics_1,
        "swing_2": metrics_2,
        "metrics": rows,
        "output_video_1": str(output1_path),
        "output_video_2": str(output2_path),
    }


def compare_swing_csvs(csv1_path, csv2_path):
    """Legacy CSV-based comparison (unchanged behaviour)."""
    swing1 = pd.read_csv(csv1_path)
    swing2 = pd.read_csv(csv2_path)

    results = {
        "swing_1": {
            "frames": len(swing1),
            "max_x_factor": float(swing1["x_factor"].max()),
            "average_x_factor": float(swing1["x_factor"].mean()),
            "max_elbow_bend": float(swing1["right_elbow_angle"].min()),
            "max_knee_bend": float(swing1["right_knee_angle"].min()),
        },
        "swing_2": {
            "frames": len(swing2),
            "max_x_factor": float(swing2["x_factor"].max()),
            "average_x_factor": float(swing2["x_factor"].mean()),
            "max_elbow_bend": float(swing2["right_elbow_angle"].min()),
            "max_knee_bend": float(swing2["right_knee_angle"].min()),
        },
    }

    results["differences"] = {
        "max_x_factor_difference": results["swing_2"]["max_x_factor"] - results["swing_1"]["max_x_factor"],
        "average_x_factor_difference": results["swing_2"]["average_x_factor"] - results["swing_1"]["average_x_factor"],
        "elbow_bend_difference": results["swing_2"]["max_elbow_bend"] - results["swing_1"]["max_elbow_bend"],
        "knee_bend_difference": results["swing_2"]["max_knee_bend"] - results["swing_1"]["max_knee_bend"],
    }

    return results
