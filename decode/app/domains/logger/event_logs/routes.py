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
# - 이벤트 로그 목록 화면을 생성하는 기능 -
# (조회, 옵션 선택, 필터, 정렬, 페이지 분할, html에 전달)
# get_event_list()를 호출한 다음, 내부의 파일을 읽어서 모든 이벤트 
# 로그를 가져옴(반환되는 데이터는 리스트 형태)
# -> 화면에 출력할 모든 이벤트 로그를 메모리로 불러오는 과정
# 사용자가 아래의 요청사항을 수정해 요청한다면, 해당 형태의 딕셔너리로
# 반환해 이벤트 데이터를 가공한 다음, 매개변수로서 전달함
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
# - 엑셀로 이벤트 로그 데이터 내보내는 기능 -
# 사용자가 해당 버튼을 누르면, 요청이 서버로 전달되고, get_event_list()를
# 호출해 event_logs.json의 모든 데이커를 가져온 뒤, format_events()를
# 호출해 영문 KEY값을 한글 KEY값으로 변환한 뒤, 메모리 상에 엑셀파일을
# 생성해 download_excel_file()을 통해 브라우저에서 event_logs.xlsx의 
# 이름으로 다운로드 됨
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
# - 'data'를 매개변수로 새로운 이벤트 로그 추가/저장하기 -
# 외부 AI 프로그램이나 다른 서버에서 json데이터를 전송하면 실행됨
# request.get_json()은 HTTP Body에 포함된 JSON을 Python의 Dictionary로 
# 변환된 뒤, 데이터는 add_event(data)로 그대로 전달되고, 저장되면 
# '201 Created' 응답을 반환함
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
# - 이벤트에 저장된 이미지 경로를 반환하는 기능 -
# 브라우저가 이벤트 로그를 클릭해 요청하면, 해당 이벤트 로그 아이디를 
# 매개변수로서 전달하고, event_logs = load_json(EVENT_LOGS_FILE)를
# 호출해 event_logs.json을 읽어서 해당되는 이벤트가 존재하는지 확인하고,
# 존재하지 않는 경우에는 '404' 오류를 반환함
# 존재하는 경우에는 이미지 경로를 jsonify를 이용해서 
# '/static/img/event_img/...' 형태의 url로 변환하고, json으로 
# 브라우저에 전달해 url을 <img> 태그의 src에 넣어서 이미지를 표시함
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
# - 선택한 이벤트 로그를 읽음 처리하는 기능 -
# 브라우저는 데이터를 post방식으로 전송하고, data = request.get_json()의
# 형식으로 데이터를 받은 다음, viewer_id = session.get("id")를
# 통해 현재 로그인한 사용자 ID를 가져오고, 비 로그인 상태라면 
# '401 Unauthorized'을 반환하지만, 로그인 상태라면 
# checked_event_logs(ids, viewer_id)를 호출해 이벤트의 
# IS_READ를 True로 변경하고, 로그인한 ID를 사용자 로그에 저장한 뒤,
# "result": "success"를 반환함
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
# - SSE(Server-Sent Events)를 이용한 실시간 이벤트 알림 기능 -
# 브라우저에서는 new EventSource("/event_log/stream_log")을 호출해
# 서버와 연결을 유지하고, 서버는 while True:를 통해 계속 실행되며,
# wait_new_log()에서 새로운 이벤트가 발생할 때까지 대기함
# 다른 곳에서 notify_new_log()가 호출되면, 대기를 종료하고,
# yield "data: new\n\n"를 실행해 브라우저에 '새 이벤트 발생'를 전송한 뒤,
# 브라우저는 메세지를 받으면, 자동으로 /event_log/new를 호출해 새로운
# 이벤트를 가져옴
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
# - 마지막으로 받은 이벤트 이후에 생성된 이벤트만 반환하는 기능 -
# 브라우저는 /event_log/new?after=UUID의 형태로 요청하고 
# after = request.args.get("after")를 통해 URL의 Query String에 
# 포함된 after값을 가져온 뒤, get_new_event_list(after)를 호출해
# 'after 이후에 생성된 이벤트'만 찾아서 반환한 뒤, jsonify(new_events)을
# 통해 json으로 변환되어 브라우저에 전달됨
# 브라우저는 전달받은 이벤트를 테이블에 추가하고, 화면 갱신 작업을 수행함
# ===========================================================
@event_log_bp.route("/new")
def get_new_events():

    after = request.args.get("after")

    new_events = get_new_event_list(after)

    return jsonify(new_events)