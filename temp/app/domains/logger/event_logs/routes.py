from flask import (Blueprint, render_template, url_for, 
                   request, Response, session, jsonify)
from app.domains.logger.event_logs.event_logs import (
    get_event_list, add_event, get_new_event_list,
    format_events,checked_event_logs)
from app.domains.logger.logger_utils.log_utils import (
    create_excel_file, download_excel_file)
from app.utils.pagination import paginate
from app.domains.logger.logger_utils.event_log_filter import (
    filter_keyword, filter_status, sort_logs)
from app.domains.logger.logger_utils.log_request_filter import(
    get_log_filter_options)
from app.domains.logger.logger_utils.event_notifier import (
    wait_new_log)
from app.utils.json_manager import (load_json, EVENT_LOGS_FILE)


event_log_bp = Blueprint(
    "event_log",
    __name__,
    url_prefix="/event_log",
    template_folder="../templates",
    static_folder="../static"
)


# ===========================================================
# 이벤트 로그 목록 화면을 생성하는 기능
# (조회, 옵션 선택, 필터, 정렬, 페이지 분할, html에 전달)
# ===========================================================
@event_log_bp.route("/log_list_event")
def event_list():

    events = get_event_list()

    options = get_log_filter_options(request)

    events = filter_keyword(
        events,
        options["keyword"],
        options["tag"])

    events = filter_status(
        events,
        options["status"])

    events = sort_logs(
        events,
        options["sort"])

    events, total_pages = paginate(
        events, 
        options["page"], 
        options["per_page"])

    return render_template(
        "log_list_event.html", 

        events = events,

        page = options["page"],
        per_page = options["per_page"],
        total_pages = total_pages,

        keyword = options["keyword"],
        tag = options["tag"],
        status = options["status"],
        sort = options["sort"],

        title = "이벤트 로그",
        description = "영상 관제 이벤트 목록",
        mode = "event",

        download_url = url_for("event_log.export_event_data")
    )
    

# ===========================================================
# 엑셀로 이벤트 로그 데이터 내보내기
# ===========================================================
@event_log_bp.route("/export_event_data")
def export_event_data():

    events = get_event_list()

    cleaned_events = format_events(events)

    output = create_excel_file(
        cleaned_events, 
        sheet_name="Event_Logs")

    return download_excel_file(
        output, 
        "event_logs.xlsx")


# ===========================================================
# 'data'를 매개로 이벤트 로그 추가하기
# ===========================================================
@event_log_bp.route("/add_event", methods=["POST"])
def add_event_log():

    data = request.get_json()

    if not data:
        return {
            "message": "Invalid JSON data"
        }, 400
     
    add_event(data)

    return {"result": "success"}, 201


# ===========================================================
# 이벤트 캡처 로그 추가하기
# ===========================================================
@event_log_bp.route("/detail/<event_id>")
def event_capture_detail(event_id):

    event_logs = load_json(EVENT_LOGS_FILE)
    event_captures = load_json(EVENT_LOGS_FILE)

    event = event_logs.get(event_id)

    if event is None:
        return jsonify({
            "result": "fail",
            "message": "존재하지 않는 이벤트입니다."
        }), 404

    capture = event_captures.get(event_id)

    if capture is None:
        return jsonify({
            "result": "fail",
            "message": "이미지가 없습니다."
        }), 404
    
    return jsonify({
        "result": "success",
        "image": url_for(
        "static",
        filename = capture["IMG_ROOT"]
        )
    })


# ===========================================================
# 이벤트 로그 선택해서 읽음 처리하기 
# ===========================================================
@event_log_bp.route("/checked_event_log", methods=["POST"])
def checked_event():

    data = request.get_json()

    viewer_id = session.get("id")

    if viewer_id is None:
        return {
            "result": "fail",
            "message": "로그인이 필요한 서비스입니다."}, 401

    ids = data.get("ids", [])

    if not ids:
        return {
            "result": "fail",
            "message": "선택된 이벤트가 없습니다."}, 400

    checked_event_logs(
        data["ids"],
        viewer_id)

    return {"result": "success"}


# ===========================================================
# SSE를 이용해 이벤트 로그가 생성되면, 서버에서 브라우저로 실시간 알림
# ===========================================================
@event_log_bp.route("/stream_log")
def stream_log():

    def stream_event_log():

        while True:
            wait_new_log()

            yield "data: new\n\n"

    return Response(
        stream_event_log(),
        mimetype = "text/event-stream",
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# ===========================================================
# 새로이 생성된 이벤트 로그의 데이터를 가져오기
# ===========================================================
@event_log_bp.route("/new")
def get_new_events():

    after = request.args.get("after")

    new_events = get_new_event_list(after)

    return jsonify(new_events)