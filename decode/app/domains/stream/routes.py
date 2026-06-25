from flask import Blueprint, Response, render_template
from app.domains.stream import camera
import time
import cv2

stream_bp = Blueprint(
    "stream", __name__, url_prefix="/stream", template_folder="templates"
)


@stream_bp.route("/")
def stream():
    return render_template("index.html")


@stream_bp.route("/video_feed/")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def generate_frames():
    while True:
        frame = camera.get_frame()

        if frame is None:
            time.sleep(0.1)
            continue

        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            time.sleep(0.1)
            continue

        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

        time.sleep(0.03)
