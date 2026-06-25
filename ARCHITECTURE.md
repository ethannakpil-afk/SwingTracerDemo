# SwingTech — Architecture Description

**SwingTech** is a web-based golf swing video analysis platform. A user uploads a
swing video; the server runs computer-vision pose estimation over it, draws
biomechanical overlays (joint angles, body-part paths), and returns an annotated
video. Users can also compare two swings side-by-side and persist results as
server-side "reports."

---

## 1. High-Level Overview

```
                         ┌──────────────────────────────────────────────┐
                         │                  BROWSER                      │
                         │  templates/index.html (HTML + CSS + vanilla   │
                         │  JS, single-page, two "screens")              │
                         │                                               │
                         │  • Single Analysis screen                     │
                         │  • Compare Swings screen                      │
                         │  • Saved Reports panel + report modal         │
                         └───────────────┬──────────────────────────────┘
                                         │  HTTP (fetch / multipart / JSON)
                                         ▼
                         ┌──────────────────────────────────────────────┐
                         │              FLASK APP (app.py)               │
                         │  Routing • request handling • file I/O •      │
                         │  JSON responses • report persistence          │
                         └───┬───────────────┬───────────────┬──────────┘
                             │               │               │
              analysis routes│        compare │         reports│
                             ▼               ▼               ▼
          ┌──────────────────────────┐  ┌───────────┐  ┌──────────────┐
          │   analysis/*.py modules  │  │ swing_    │  │ reports/     │
          │   (OpenCV + MediaPipe +  │  │ metrics + │  │ *.json       │
          │   FFmpeg per metric)     │  │ compare   │  │ (on disk)    │
          └──────────────────────────┘  └───────────┘  └──────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────────┐
          │  File system                              │
          │  uploads/           (raw input videos)    │
          │  static/outputs/    (annotated MP4s)      │
          │  reports/           (saved report JSON)   │
          └──────────────────────────────────────────┘
```

**Architecture style:** classic server-rendered **monolithic web app** with a
thin single-page frontend. There is no database; all state lives on the file
system. Heavy lifting (CV inference) happens synchronously inside request
handlers.

---

## 2. Technology Stack

| Layer            | Technology                                              |
|------------------|---------------------------------------------------------|
| Web framework    | Flask 3.1 (Werkzeug 3.1)                                 |
| CV / pose model  | MediaPipe Pose 0.10.21                                   |
| Image/video I/O  | OpenCV (`opencv-python` 4.x)                             |
| Video transcode  | FFmpeg (external CLI, invoked via `subprocess`)          |
| Numerics / data  | NumPy 1.26, pandas 3.0 (CSV compare path)               |
| Frontend         | Single HTML file: inline CSS + vanilla JavaScript        |
| Runtime          | Python 3.12 virtual env (`.venv/`)                       |
| Server           | Flask dev server, `debug=True`, port **5031**            |

Dependencies are pinned in `requirements.txt`.

---

## 3. Directory Layout

```
Swing Tracer Demo/
├── app.py                     # Flask application: all routes + persistence
├── requirements.txt           # Pinned Python dependencies
├── ARCHITECTURE.md            # This document
│
├── analysis/                  # Computer-vision analysis modules
│   ├── swing_metrics.py       # Shared extractor (metrics + annotated video)
│   ├── compareanalytics.py    # Two-swing comparison (video + legacy CSV)
│   ├── elbow.py               # Per-metric analyzers (one function each)
│   ├── headstability.py
│   ├── hiprotation.py
│   ├── kneeflex.py
│   ├── posture.py
│   ├── shoulderturn.py
│   ├── swingphase.py
│   ├── wristpath.py
│   └── xfactor.py
│
├── templates/
│   └── index.html             # Entire frontend (SPA-style)
│
├── static/
│   └── outputs/               # Annotated result videos (served to browser)
│
├── uploads/                   # Raw uploaded input videos
├── reports/                   # Persisted report records (<id>.json)
└── .venv/                     # Python 3.12 virtual environment
```

---

## 4. Backend (`app.py`)

The Flask app is the single orchestration point. On import it:

1. Resolves `BASE_DIR` and ensures `uploads/`, `static/outputs/`, and
   `reports/` exist.
2. Imports each analysis function from `analysis/`.
3. Registers all routes.

### 4.1 Route Map

| Route                       | Method | Purpose                                              |
|-----------------------------|--------|------------------------------------------------------|
| `/`                         | GET    | Render `index.html`                                  |
| `/analyze/headstability`    | POST   | Head drift tracking                                  |
| `/analyze/elbow`            | POST   | Elbow angle                                          |
| `/analyze/posture`          | POST   | Spine angle / tilt                                   |
| `/analyze/kneeflex`         | POST   | Knee flex angle                                      |
| `/analyze/wristpath`        | POST   | Wrist/club path trace                                |
| `/analyze/swingphase`       | POST   | Swing phase segmentation                             |
| `/analyze/shoulderturn`     | POST   | Shoulder rotation                                    |
| `/analyze/hipturn`          | POST   | Hip rotation                                         |
| `/analyze/xfactor`          | POST   | Hip-vs-shoulder separation (X-Factor)                |
| `/analyze/compareanalytics` | POST   | Legacy CSV-based comparison (two CSV files)          |
| `/compare`                  | POST   | Two-video comparison (annotated videos + metrics)    |
| `/reports`                  | GET    | List saved report summaries (newest first)           |
| `/reports`                  | POST   | Persist a report to disk                             |
| `/reports/<id>`             | GET    | Fetch one full report                                |
| `/reports/<id>`             | DELETE | Delete a report                                      |
| `/static/<path>`            | GET    | Serve static assets (incl. output videos)            |

### 4.2 Single-Analysis Request Flow

```
Browser (multipart "video")
   │  POST /analyze/<metric>
   ▼
Flask handler
   │  1. Validate "video" present and named
   │  2. secure_filename() + build input/output paths
   │  3. Save upload to uploads/
   │  4. Call run_<metric>_analysis(input_path, output_path)
   │       └─ OpenCV reads frames → MediaPipe Pose → draw overlays
   │          → VideoWriter (mp4v) → FFmpeg re-encode to H.264
   │  5. Verify output exists
   ▼
JSON { "output_video": "/static/outputs/<metric>_output_<n>.mp4" }
   │
   ▼
Browser sets <video src> to the result and shows it
```

Each handler follows the same defensive pattern: validate input, run analysis,
check that the output file was actually created, and on any exception print a
full traceback server-side and return `{ "error": ... }` with a 4xx/5xx status.

### 4.3 Compare Request Flow (`/compare`)

```
Browser (multipart "video1" + "video2")
   │  POST /compare
   ▼
Flask compare_videos()
   │  Save both inputs → uploads/
   │  compare_swing_videos(in1,out1,in2,out2)
   │     └─ extract_swing_metrics() on EACH video:
   │           pose inference + overlays + annotated MP4
   │           + summary metrics (max/avg x-factor, min elbow,
   │             min knee, max shoulder/hip turn, tracked frames)
   │     └─ build per-metric comparison rows w/ differences
   ▼
JSON {
  swing_1:{...}, swing_2:{...},
  metrics:[{label,unit,swing_1,swing_2,difference}...],
  output_video_1, output_video_2
}
```

### 4.4 Reports Persistence

Reports are stored as individual JSON files in `reports/`, named by a random
12-char id. No database. Each record:

```json
{
  "id":      "ab12cd34ef56",
  "type":    "analysis" | "compare",
  "title":   "Human-readable label",
  "created": "ISO-8601 timestamp",
  "data":    { ... arbitrary report payload ... }
}
```

- `POST /reports` generates the id + timestamp and writes the file.
- `GET /reports` globs `reports/*.json`, returns lightweight summaries
  (id/type/title/created), sorted newest-first.
- `GET /reports/<id>` returns the full record.
- `DELETE /reports/<id>` removes the file.
- Path parameters are passed through `secure_filename()` to prevent traversal.

---

## 5. Analysis Layer (`analysis/`)

### 5.1 Per-Metric Modules

Each module (`elbow.py`, `kneeflex.py`, `posture.py`, `headstability.py`,
`wristpath.py`, `xfactor.py`, `shoulderturn.py`, `hiprotation.py`,
`swingphase.py`) exposes a single `run_<metric>_analysis(input_path,
output_path)` function and follows an identical pipeline:

```
1. Initialize MediaPipe Pose + drawing utils
2. Open input video with cv2.VideoCapture
3. Read frame dimensions + FPS
4. Open a temp VideoWriter (mp4v codec)
5. For each frame:
     a. BGR → RGB
     b. pose.process() to get landmarks
     c. draw skeleton + metric-specific overlays
        (lines, circles, angle/value text, motion paths)
     d. write frame
6. Release capture/writer, close pose
7. subprocess FFmpeg: re-encode temp mp4v → H.264 (yuv420p)
   so the result plays in browsers
8. Delete temp file, return output_path
```

The **FFmpeg re-encode step is essential**: OpenCV's `mp4v` output is not
reliably playable in browsers, so every module transcodes to H.264 yuv420p.

Metric-specific logic examples:
- **elbow / kneeflex** — three-point interior angle (shoulder-elbow-wrist,
  hip-knee-ankle).
- **xfactor** — angle of the shoulder line vs. the hip line (rotational
  separation).
- **posture** — spine tilt from shoulder-to-hip vector vs. vertical.
- **headstability** — tracks the nose landmark, draws cumulative path and
  pixel drift from the starting position.
- **wristpath** — accumulates and draws the right-wrist trajectory.

### 5.2 Shared Extractor (`swing_metrics.py`)

`extract_swing_metrics(input_path, output_path)` is a consolidated extractor
used by the compare feature. In a single pass it computes X-Factor, elbow angle,
knee angle, and shoulder/hip turn, draws combined overlays, writes an annotated
H.264 video, and returns a summary metric dict (max/avg/min aggregates +
tracked-frame count). This avoids running the video through pose estimation
multiple times for a comparison.

### 5.3 Compare Module (`compareanalytics.py`)

Two entry points:
- `compare_swing_videos(...)` — runs `extract_swing_metrics` on both videos and
  builds the structured comparison (per-metric rows with deltas). Used by
  `/compare`.
- `compare_swing_csvs(...)` — legacy pandas-based comparison of two exported CSV
  files. Used by `/analyze/compareanalytics`. Retained for backward
  compatibility.

---

## 6. Frontend (`templates/index.html`)

A single self-contained page (inline CSS + vanilla JS, no build step, no
framework). It behaves as a small SPA with two switchable "screens."

### 6.1 Structure

- **Mode tabs** — toggle between *Single Analysis* and *Compare Swings*
  (CSS class `.active` shows/hides each `.screen`).
- **Single Analysis screen**
  - Drag-and-drop / click upload box with live local preview.
  - In-browser **Media Library** (client-side only) listing uploaded files.
  - Grid of analysis tool buttons (built dynamically from a `TOOLS` array with
    inline SVG icons).
  - On result: shows annotated video, **Download** and **Save Data** buttons,
    and a status indicator.
- **Compare Swings screen**
  - Two side-by-side upload panels (Swing A / Swing B).
  - **Run Comparison** → `POST /compare`.
  - Renders both annotated result videos plus a **metric comparison table**
    with color-coded differences.
  - **Download Both Videos** and **Save Data** actions.
- **Saved Reports panel** (shared across both modes)
  - Lists server-side reports with type badge, title, timestamp.
  - **View** (opens a modal with the full JSON payload), **Delete**, **Refresh**.

### 6.2 Client–Server Interaction

| UI action                  | Request                                  | Response handling                          |
|----------------------------|------------------------------------------|--------------------------------------------|
| Run single analysis        | `POST /analyze/<metric>` (multipart)     | Set `<video>` to returned `output_video`   |
| Run comparison             | `POST /compare` (multipart x2)           | Show both videos + render metrics table    |
| Save Data (single/compare) | `POST /reports` (JSON)                    | Refresh Saved Reports list                 |
| View / Delete / Refresh    | `GET|DELETE /reports[/<id>]`             | Populate modal / reload list               |

A full-screen loading overlay with an animated progress bar is shown during the
(synchronous, potentially slow) analysis and compare requests.

---

## 7. Data & Control Flow Summary

1. **Upload** → browser holds the file locally, previews it.
2. **Analyze/Compare** → file(s) POSTed to Flask, saved under `uploads/`.
3. **Process** → analysis module(s) run MediaPipe over every frame, draw
   overlays, write an `mp4v` temp file, then FFmpeg-transcode to browser-safe
   H.264 in `static/outputs/`.
4. **Respond** → Flask returns JSON with the static URL(s) (+ metrics for
   compare).
5. **Display** → browser plays the annotated result; compare also renders a
   difference table.
6. **Persist (optional)** → "Save Data" POSTs a report; Flask writes
   `reports/<id>.json`; the Saved Reports panel reflects it and can view/delete
   it later.

---

## 8. Key Design Characteristics & Constraints

- **No database** — all persistence is flat files (videos + report JSON). Simple
  and portable; not concurrent-write safe or horizontally scalable.
- **Synchronous CV in request handlers** — analysis blocks the request for its
  full duration. Fine for a local/demo single-user tool; would need a task queue
  (e.g. Celery/RQ) for production or concurrent users.
- **FFmpeg dependency** — must be installed and on `PATH`; every result video is
  transcoded for browser compatibility.
- **Fixed output filenames** — `/compare` and several analysis routes write to
  deterministic names (e.g. `compare_output_1.mp4`), so concurrent runs can
  overwrite each other.
- **Dev server / debug mode** — runs Flask's development server with
  `debug=True` on port 5031; not intended for production deployment as-is.
- **Right-side bias** — most single-metric analyzers use right-side landmarks,
  implicitly assuming a particular camera orientation / handedness.

---

## 9. Running the Project

```bash
cd "Swing Tracer Demo"
.venv/bin/python app.py        # http://127.0.0.1:5031
```

Requirements: the `.venv` (Python 3.12) with `requirements.txt` installed, and
FFmpeg available on the system `PATH`.
```
