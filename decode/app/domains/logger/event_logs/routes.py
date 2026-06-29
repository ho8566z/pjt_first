from flask import Blueprint, render_template
from logger.event_logs.event_logs import get_event_list
from app.domains.logger.event_logs.event_log_utils import (
    format_events, create_excel_file, download_excel_file)

event_log_bp = Blueprint(
    "event_log", __name__, url_prefix="/event_log", template_folder="templates"
)


@event_log_bp.route("/event_log_list")
def event_list():

    events = get_event_list()

    return render_template("event_log_list.html", events=events)
    

@event_log_bp.route("/export_data")
def export_data():
    events = get_event_list()

    cleaned_events = format_events(events)

    output = create_excel_file(cleaned_events)

    return download_excel_file(output)

