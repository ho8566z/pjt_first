import time

from flask import Blueprint, Response, render_template, request, redirect, url_for
from app.domains.stream import profile_service
from cv2 import imencode

from app.domains.stream import analysis_pipeline
from app.domains.stream import camera as camera_manager


stream_bp = Blueprint(
    "stream",
    __name__,
    url_prefix="/stream",
    template_folder="templates",
    static_folder="static",
    static_url_path="/stream/static",
)


@stream_bp.route("/monitoring")
def monitoring():
    camera_ids = camera_manager.get_all_camera_ids()
    return render_template("stream_main.html", camera_ids=camera_ids)


@stream_bp.route("/camera/", methods=["GET", "POST"])
def camera():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            cam_id = request.form.get("cam_id")
            src_path = request.form.get("src_path")
            src_type = request.form.get("src_type", "video")  # 기본값은 video

            if cam_id and src_path:
                camera_manager.add_camera(
                    src_path=src_path, id=cam_id, src_type=src_type
                )

        elif action == "delete":
            cam_id = request.form.get("cam_id")
            if cam_id:
                camera_manager.delete_camera(cam_id)

        return redirect(url_for("stream.camera"))

    active_cameras = []
    for cid in camera_manager.get_all_camera_ids():
        cam_obj = camera_manager.get_camera_by_id(cid)
        if cam_obj:
            active_cameras.append(
                {"id": cid, "src_path": cam_obj.src_path, "is_video": cam_obj.is_video}
            )

    return render_template("camera_main.html", cameras=active_cameras)


@stream_bp.route("/profile/", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            profile_service.handle_add_profile(
                request.form, request.files, stream_bp.static_folder
            )

        elif action == "update":
            profile_service.handle_update_profile(
                request.form, request.files, stream_bp.static_folder
            )

        elif action == "face_encode":
            profile_service.handle_face_encode(request.form, request.files)

        elif action == "delete":
            profile_service.handle_delete_profile(request.form)

        return redirect(url_for("stream.profile"))

    profiles_paginated, page, per_page, total_pages = (
        profile_service.get_paginated_profiles(request.args)
    )

    return render_template(
        "profile_main.html",
        profiles=profiles_paginated,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@stream_bp.route("/video_feed/")
def video_feed():

    cam_id = request.args.get("cam_id", "0")

    return Response(
        generate_frames(cam_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def generate_frames(cam_id):
    while True:
        frames = analysis_pipeline.get_latest_frames()
        frame = frames[cam_id]

        if frame is None:
            time.sleep(0.1)
            continue

        ret, buffer = imencode(".jpg", frame)

        if not ret:
            time.sleep(0.1)
            continue

        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.01)
