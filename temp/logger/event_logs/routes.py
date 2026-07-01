from flask import Blueprint, render_template, request
from app.domains.logger.event_logs.event_logs import (
    get_event_list,add_event,format_events)
from app.domains.logger.logger_utils.log_utils import (
    create_excel_file, download_excel_file)


event_log_bp = Blueprint(
    "event_log",
    __name__,
    url_prefix="/event_log",
    template_folder="../templates",
    static_folder="../static"
)

@event_log_bp.route("/event_log_list")
def event_list():

    events = get_event_list()

    return render_template(
        "event_log_list.html", 
        events = events)
    

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
