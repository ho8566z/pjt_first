from flask import (Blueprint, render_template, 
                   url_for, request, session)
from app.domains.logger.event_logs.event_logs import (
    get_event_list, add_event, format_events,
    checked_event_logs)
from app.domains.logger.logger_utils.log_utils import (
    create_excel_file, download_excel_file)
from app.utils.pagination import paginate
from app.domains.logger.logger_utils.event_log_filter import (
    filter_keyword, filter_status, sort_logs)
from app.domains.logger.logger_utils.log_request_filter import(
    get_log_filter_options)


event_log_bp = Blueprint(
    "event_log",
    __name__,
    url_prefix="/event_log",
    template_folder="../templates",
    static_folder="../static"
)

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


@event_log_bp.route("/add_event", methods=["POST"])
def add_event_log():

    data = request.get_json()

    if not data:
        return {
            "result": "fail", 
            "message": "Invalid JSON data"
        }, 400
     
    add_event(data)

    return {"result": "success"}, 201


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