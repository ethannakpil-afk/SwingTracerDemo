# SwingTech — Golf Swing Video Analysis Platform

SwingTech is a web app that analyzes golf swing videos using computer-vision pose
estimation. Upload a swing, and the server tracks body landmarks frame-by-frame,
draws biomechanical overlays (joint angles, body-part paths), and returns an
annotated video. You can also compare two swings side-by-side and save results as
reports.

## Features

- **9 analysis tools** — Head Stability, Elbow Angle, Posture, Knee Flex, Wrist
  Path, Swing Phase, Shoulder Turn, Hip Rotation, and X-Factor.
- **Side-by-side comparison** — upload two swings, run both, and view annotated
  videos plus a metric comparison table with differences.
- **Saved Reports** — persist analysis and comparison results server-side, then
  view or delete them later.
- **Annotated output** — each result video is re-encoded to browser-friendly
  H.264.

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Web framework    | Flask                               |
| Pose estimation  | MediaPipe Pose                      |
| Image/video I/O  | OpenCV                              |
| Video transcode  | FFmpeg (external CLI)               |
| Numerics / data  | NumPy, pandas                       |
| Frontend         | Vanilla HTML + CSS + JavaScript     |

## Prerequisites

- **Python 3.12**
- **FFmpeg** installed and available on your system `PATH`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/ethannakpil-afk/SwingTracerDemo.git
cd SwingTracerDemo

# 2. Create a virtual environment (Python 3.12)
python3.12 -m venv .venv

# 3. Install dependencies
.venv/bin/pip install -r requirements.txt
```

## Running

```bash
.venv/bin/python app.py
```

Then open **http://127.0.0.1:5031** in your browser.

## Usage

1. **Single Analysis** — upload a swing video, then click any analysis tool. The
   annotated result plays in the preview. Use **Download** to save the video or
   **Save Data** to store a report.
2. **Compare Swings** — switch to the Compare tab, upload a video into each
   panel, and click **Run Comparison**. View both annotated videos, the metric
   comparison table, and download/save the results.
3. **Saved Reports** — saved analyses and comparisons appear in the Saved Reports
   panel, where you can view or delete them.

## Project Structure

```
SwingTracerDemo/
├── app.py                 # Flask application: routes + report persistence
├── requirements.txt       # Python dependencies
├── ARCHITECTURE.md        # Detailed architecture description
│
├── analysis/              # Computer-vision analysis modules
│   ├── swing_metrics.py   # Shared metrics extractor (used by compare)
│   ├── compareanalytics.py
│   └── *.py               # One analyzer per metric
│
├── templates/
│   └── index.html         # Frontend (single-page app)
│
├── static/outputs/        # Generated annotated videos (runtime)
├── uploads/               # Uploaded input videos (runtime)
└── reports/               # Saved report JSON files (runtime)
```

For a full breakdown of the design, request flows, and data model, see
[ARCHITECTURE.md](ARCHITECTURE.md).

## Notes

- The app runs on Flask's development server (`debug=True`, port `5031`) and is
  intended for local / single-user use.
- Uploaded and generated videos are stored on the file system and are excluded
  from version control.
