from flask import Flask, render_template, request, jsonify
from pathlib import Path
import traceback
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from analysis.elbow import run_elbow_analysis
from analysis.shoulderturn import run_shoulderturn_analysis
from analysis.swingphase import run_swingphase_analysis
from analysis.hiprotation import run_hipturn_analysis
from analysis.kneeflex import run_kneeflex_analysis
from analysis.xfactor import run_xfactor_analysis
from analysis.posture import run_posture_analysis
from analysis.headstability import run_headstability_analysis
from analysis.wristpath import run_wristpath_analysis
from analysis.compareanalytics import compare_swing_csvs, compare_swing_videos

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "static" / "outputs"
REPORTS_DIR = BASE_DIR / "reports"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


def run_video_analysis(analysis_name, analysis_function):
    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")
        safe_filename = secure_filename(video.filename)

        input_filename = f"{analysis_name}_input_video_{video_number}_{safe_filename}"
        output_filename = f"{analysis_name}_output_video_{video_number}.mp4"

        input_path = UPLOAD_DIR / input_filename
        output_path = OUTPUT_DIR / output_filename

        video.save(str(input_path))

        result = analysis_function(input_path, output_path)

        if result is None:
            return jsonify({"error": f"{analysis_name} analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": f"{analysis_name} output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/{output_filename}"
        })

    except Exception as e:
        print(f"{analysis_name.upper()} ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/elbow", methods=["POST"])
def analyze_elbow():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"elbow_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_elbow_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Elbow analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/elbow_output_{video_number}.mp4"
        })

    except Exception as e:
        print("ELBOW ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/analyze/shoulderturn", methods=["POST"])
def analyze_shoulderturn():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"shoulderturn_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_shoulderturn_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Shoulder turn analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Shoulder turn output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/shoulderturn_output_{video_number}.mp4"
        })

    except Exception as e:
        print("SHOULDER TURN ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/swingphase", methods=["POST"])
def analyze_swingphase():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"swingphase_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_swingphase_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Swing phase analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Swing phase output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/swingphase_output_{video_number}.mp4"
        })

    except Exception as e:
        print("SWING PHASE ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/hipturn", methods=["POST"])
def analyze_hipturn():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"hipturn_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_hipturn_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Hip turn analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Hip turn output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/hipturn_output_{video_number}.mp4"
        })

    except Exception as e:
        print("HIP TURN ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/kneeflex", methods=["POST"])
def analyze_kneeflex():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"kneeflex_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_kneeflex_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Knee flex analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Knee flex output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/kneeflex_output_{video_number}.mp4"
        })

    except Exception as e:
        print("KNEE FLEX ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/xfactor", methods=["POST"])
def analyze_xfactor():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"xfactor_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_xfactor_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "X-Factor analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "X-Factor output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/xfactor_output_{video_number}.mp4"
        })

    except Exception as e:
        print("X-FACTOR ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/analyze/posture", methods=["POST"])
def analyze_posture():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"posture_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_posture_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Posture analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Posture output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/posture_output_{video_number}.mp4"
        })

    except Exception as e:
        print("POSTURE ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/headstability", methods=["POST"])
def analyze_headstability():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"headstability_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_headstability_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Head stability analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Head stability output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/headstability_output_{video_number}.mp4"
        })

    except Exception as e:
        print("HEAD STABILITY ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/wristpath", methods=["POST"])
def analyze_wristpath():

    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file received"}), 400

        video = request.files["video"]

        if video.filename == "":
            return jsonify({"error": "No selected video"}), 400

        video_number = request.form.get("video_number", "1")

        input_path = UPLOAD_DIR / f"video_{video_number}_{video.filename}"
        output_path = OUTPUT_DIR / f"wristpath_output_{video_number}.mp4"

        video.save(str(input_path))

        result = run_wristpath_analysis(input_path, output_path)

        if result is None:
            return jsonify({"error": "Wrist path analysis failed"}), 500

        if not output_path.exists():
            return jsonify({"error": "Wrist path output video was not created"}), 500

        return jsonify({
            "output_video": f"/static/outputs/wristpath_output_{video_number}.mp4"
        })

    except Exception as e:
        print("WRIST PATH ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/analyze/compareanalytics", methods=["POST"])
def analyze_compareanalytics():

    try:
        if "csv1" not in request.files or "csv2" not in request.files:
            return jsonify({"error": "Two CSV files are required"}), 400

        csv1 = request.files["csv1"]
        csv2 = request.files["csv2"]

        csv1_path = UPLOAD_DIR / csv1.filename
        csv2_path = UPLOAD_DIR / csv2.filename

        csv1.save(str(csv1_path))
        csv2.save(str(csv2_path))

        results = compare_swing_csvs(csv1_path, csv2_path)

        return jsonify(results)

    except Exception as e:
        print("COMPARE ANALYTICS ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/compare", methods=["POST"])
def compare_videos():

    try:
        if "video1" not in request.files or "video2" not in request.files:
            return jsonify({"error": "Two videos are required"}), 400

        video1 = request.files["video1"]
        video2 = request.files["video2"]

        if video1.filename == "" or video2.filename == "":
            return jsonify({"error": "Both videos must be selected"}), 400

        name1 = secure_filename(video1.filename)
        name2 = secure_filename(video2.filename)

        input1_path = UPLOAD_DIR / f"compare_input_1_{name1}"
        input2_path = UPLOAD_DIR / f"compare_input_2_{name2}"
        output1_path = OUTPUT_DIR / "compare_output_1.mp4"
        output2_path = OUTPUT_DIR / "compare_output_2.mp4"

        video1.save(str(input1_path))
        video2.save(str(input2_path))

        results = compare_swing_videos(
            input1_path, output1_path,
            input2_path, output2_path,
        )

        if not output1_path.exists() or not output2_path.exists():
            return jsonify({"error": "Comparison output videos were not created"}), 500

        results["output_video_1"] = "/static/outputs/compare_output_1.mp4"
        results["output_video_2"] = "/static/outputs/compare_output_2.mp4"

        return jsonify(results)

    except Exception as e:
        print("COMPARE ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# =====================================================================
# SAVED REPORTS (server-side persistence)
# =====================================================================

def _report_summary(data):
    """Build a small summary dict for listing without loading full payload."""
    return {
        "id": data.get("id"),
        "type": data.get("type"),
        "title": data.get("title"),
        "created": data.get("created"),
    }


@app.route("/reports", methods=["GET"])
def list_reports():
    """Return a list of saved report summaries, newest first."""
    try:
        reports = []
        for f in REPORTS_DIR.glob("*.json"):
            try:
                with open(f, "r") as fh:
                    data = json.load(fh)
                reports.append(_report_summary(data))
            except Exception:
                continue
        reports.sort(key=lambda r: r.get("created", ""), reverse=True)
        return jsonify({"reports": reports})
    except Exception as e:
        print("LIST REPORTS ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/reports", methods=["POST"])
def save_report():
    """Persist a report to disk. Expects JSON with at least 'type'."""
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({"error": "Invalid report data"}), 400

        report_type = payload.get("type", "analysis")
        title = payload.get("title") or f"{report_type.title()} report"

        report_id = uuid.uuid4().hex[:12]
        record = {
            "id": report_id,
            "type": report_type,
            "title": title,
            "created": datetime.now().isoformat(timespec="seconds"),
            "data": payload.get("data", {}),
        }

        out_path = REPORTS_DIR / f"{report_id}.json"
        with open(out_path, "w") as fh:
            json.dump(record, fh, indent=2)

        return jsonify({"saved": True, "report": _report_summary(record)})
    except Exception as e:
        print("SAVE REPORT ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/reports/<report_id>", methods=["GET"])
def get_report(report_id):
    """Return the full report record."""
    safe_id = secure_filename(report_id)
    path = REPORTS_DIR / f"{safe_id}.json"
    if not path.exists():
        return jsonify({"error": "Report not found"}), 404
    try:
        with open(path, "r") as fh:
            return jsonify(json.load(fh))
    except Exception as e:
        print("GET REPORT ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/reports/<report_id>", methods=["DELETE"])
def delete_report(report_id):
    """Delete a saved report."""
    safe_id = secure_filename(report_id)
    path = REPORTS_DIR / f"{safe_id}.json"
    if not path.exists():
        return jsonify({"error": "Report not found"}), 404
    try:
        path.unlink()
        return jsonify({"deleted": True})
    except Exception as e:
        print("DELETE REPORT ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5031)