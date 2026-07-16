import os

from flask import (
    Blueprint,  # 라우터 그룹 생성
    render_template,  # HTML 화면 출력
    request,  # 폼 데이터 접근
    session,  # 로그인 상태 저장
    redirect,  # URL 이동
    url_for,  # 함수 기반 URL 생성
    jsonify,
)

# CAPTCHA 생성 서비스
from app.domains.account.service.captcha_creator import make_captcha

# 인증 서비스 (로그인 / 비밀번호 변경 / 세션)
from app.domains.account.service.auth_service import (
    login,
    change_password,
    login_fail_session,
    create_login_session,
)

# 전역 설정값
from app import configs
from app.domains.main.dashboard_service import get_dashboard_data
from app.utils.json_manager import EVENT_LOGS_FILE


# ==========================================================
# Blueprint 생성
# ==========================================================
main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/main/static",
)


# ==========================================================
# 메인 페이지 (로그인 화면)
# ==========================================================
@main_bp.route("/")
def main():

    # 기존 로그인 세션 초기화 (로그아웃 상태)
    session.clear()

    # 로그인 화면 출력
    return render_template("main_index.html")


# ==========================================================
# 로그인 처리
# ==========================================================
@main_bp.route("/login", methods=["POST"])
def login_result():

    # 사용자 입력값으로 로그인 검증
    success, message, user = login(
        request.form["uId"], request.form["uPw"], request.form.get("captcha", "")
    )

    # =========================
    # 로그인 성공 처리
    # =========================
    if success:
        # 세션 생성 (로그인 정보 저장)
        create_login_session(user)

        # 승인 대기 계정
        if message == "pending":
            return render_template("pending.html")

        # 최초 로그인 (비밀번호 변경 필요)
        # if user[configs.KEY_IS_FIRST_LOGIN]:
        #     return render_template("first_login_form.html")

        # 일반 로그인 성공 → 대시보드 이동
        return redirect(url_for("main.dashboard"))

    # =========================
    # 로그인 실패 처리
    # =========================
    if message in ("없는 회원입니다.", "비밀번호가 틀렸습니다."):
        # 실패 횟수 증가
        login_fail, message = login_fail_session(message)

        # 실패 메시지 출력 (횟수 포함)
        message = f"{message} ({login_fail}/{configs.LOGIN_FAIL_LIMIT})"

        # CAPTCHA 활성화 조건
        if login_fail == configs.LOGIN_FAIL_LIMIT:
            make_captcha()
            message = "비밀번호 3회 실패로 자동입력 방지가 활성화되었습니다."

    # 로그인 실패 화면 출력
    return render_template("main_index.html", message=message, success=False)


# ==========================================================
# 로그아웃 처리
# ==========================================================
@main_bp.route("/signout_confirm", methods=["GET"])
def signout_confirm():

    # 세션 삭제
    session.clear()

    # 메인으로 이동
    return redirect(url_for("main.main"))


# ==========================================================
# 최초 로그인 비밀번호 변경
# ==========================================================
@main_bp.route("/first_login_form", methods=["POST"])
def first_login_form():

    # 비밀번호 변경 요청 처리
    success, message = change_password(
        session["id"],  # 현재 로그인 사용자
        request.form["oPw"],  # 기존 비밀번호
        request.form["nPw"],  # 새 비밀번호
        request.form["nPwCheck"],  # 새 비밀번호 확인
    )

    # =========================
    # 변경 성공
    # =========================
    if success:
        return render_template("main_index.html", message=message, success=True)

    # =========================
    # 변경 실패
    # =========================
    return render_template("first_login_form.html", message=message, success=False)


@main_bp.route("/createaccount", methods=["GET", "POST"])
def create_account():
    return render_template("create_account.html")


# ==========================================================
# 시스템 대시보드
# ==========================================================
def _resolve_selected_camera_id(dashboard_data):
    camera_ids = dashboard_data.get("camera_ids", [])
    requested_camera_id = request.args.get("camera_id")

    selected_camera_id = None
    if requested_camera_id is not None:
        for camera_id in camera_ids:
            if str(camera_id) == str(requested_camera_id):
                selected_camera_id = camera_id
                break

    if selected_camera_id is None:
        previous_primary_camera_id = dashboard_data.get("primary_camera_id")
        if previous_primary_camera_id in camera_ids:
            selected_camera_id = previous_primary_camera_id
        elif camera_ids:
            selected_camera_id = camera_ids[0]

    dashboard_data["primary_camera_id"] = selected_camera_id
    return dashboard_data


@main_bp.route("/dashboard")
def dashboard():

    # 로그인하지 않은 사용자는 로그인 화면으로 이동
    if "id" not in session:
        return redirect(url_for("main.main"))

    dashboard_data = _resolve_selected_camera_id(get_dashboard_data())
    event_logs_path = EVENT_LOGS_FILE
    dashboard_data["event_logs_mtime"] = (
        os.path.getmtime(event_logs_path) if os.path.exists(event_logs_path) else 0
    )

    return render_template(
        "dashboard.html",
        **dashboard_data,
    )


@main_bp.route("/dashboard/refresh")
def dashboard_refresh():
    if "id" not in session:
        return jsonify({"success": False}), 401

    dashboard_data = _resolve_selected_camera_id(get_dashboard_data())
    event_logs_path = EVENT_LOGS_FILE
    current_mtime = (
        os.path.getmtime(event_logs_path) if os.path.exists(event_logs_path) else 0
    )
    dashboard_data["event_logs_mtime"] = current_mtime

    last_seen_mtime = request.args.get("last_seen_mtime")
    changed = True
    try:
        if last_seen_mtime is not None:
            changed = float(last_seen_mtime) != current_mtime
    except (TypeError, ValueError):
        changed = True

    if not changed:
        return jsonify(
            {
                "success": True,
                "changed": False,
                "event_logs_mtime": current_mtime,
            }
        )

    html = render_template("dashboard_content.html", **dashboard_data)

    return jsonify(
        {
            "success": True,
            "changed": True,
            "html": html,
            "stats": {
                "unread_event_count": dashboard_data["stats"]["unread_event_count"],
                "target_count": dashboard_data["stats"]["target_count"],
            },
            "latest_event": dashboard_data["recent_events"][0]
            if dashboard_data["recent_events"]
            else None,
            "map_data": dashboard_data.get("map_data", []),
            "event_logs_mtime": current_mtime,
        }
    )
