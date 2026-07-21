import time

from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
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
        cam_id = request.form.get("cam_id")
        action = request.form.get("action")

        if action == "add":
            src_path = request.form.get("src_path")
            src_type = request.form.get("src_type", "video")  # 기본값은 video

            if cam_id and src_path:
                success = camera_manager.add_camera(
                    src_path=src_path, id=cam_id, src_type=src_type
                )

                if not success:
                    flash(
                        "이미 존재하는 고유 ID입니다. 다른 ID를 입력해주세요.", "error"
                    )

        elif action == "start":
            camera_manager.start_camera(cam_id)

        elif action == "stop":
            camera_manager.stop_camera(cam_id)
            print("stop!")
            print(camera_manager.is_paused_camera(cam_id))

        elif action == "delete":
            if cam_id:
                camera_manager.delete_camera(cam_id)

        return redirect(url_for("stream.camera"))

    active_cameras = []
    for cid in camera_manager.get_all_camera_ids():
        cam_obj = camera_manager.get_camera_by_id(cid)
        if cam_obj:
            active_cameras.append(
                {
                    "id": cid,
                    "src_path": cam_obj.src_path,
                    "is_video": camera_manager.is_video_camera(cid),
                    "is_paused": camera_manager.is_paused_camera(cid),
                }
            )

    return render_template("camera_main.html", cameras=active_cameras)


@stream_bp.route("/profile/", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            success = profile_service.handle_add_profile(
                request.form, request.files, stream_bp.static_folder
            )

            if not success:
                flash("이미 존재하는 고유 ID입니다. 다른 ID를 입력해주세요.", "error")

        elif action == "update":
            profile_service.handle_update_profile(
                request.form, request.files, stream_bp.static_folder
            )

        elif action == "face_encode":
            profile_service.handle_face_encode(request.form, request.files)

        elif action == "delete":
            profile_service.handle_delete_profile(request.form, stream_bp.static_folder)

        return redirect(url_for("stream.profile"))

    profiles_paginated, page, per_page, total_pages = (
        profile_service.get_paginated_profiles(request.args)
    )

    search_keyword = request.args.get("search_keyword")

    return render_template(
        "profile_main.html",
        profiles=profiles_paginated,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        search_tag=request.args.get("search_tag"),
        search_keyword=search_keyword if search_keyword else "",
        sort_order=request.args.get("sort_order"),
    )


@stream_bp.route("/video_feed/")
def video_feed():

    cam_id = request.args.get("cam_id", "0")

    return Response(
        generate_frames(cam_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def generate_frames(cam_id):
    # URL 쿼리 값은 문자열이므로 숫자 ID로 등록된 카메라도 찾을 수 있게 한다.
    camera_key = int(cam_id) if str(cam_id).isdigit() else cam_id

    while True:
        frames = analysis_pipeline.get_latest_frames()
        frame = frames.get(cam_id)

        if frame is None:
            frame = frames.get(camera_key)

        # AI 분석 스레드가 준비되는 동안에는 카메라 원본 프레임을 사용한다.
        if frame is None:
            frame = camera_manager.get_frame_by_id(camera_key)

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
