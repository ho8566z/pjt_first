from flask import Blueprint, render_template, send_file
from logger.event_logs import event_logs, get_event_list
import pandas as pd
import io

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

    cleaned_events = []
    for event in events:
        place_strings = []
        for p in event.get("PLACE", []):
            place_strings.append(
                f"{p.get('latitude')}, {p.get('longitude')}, {p.get('altitude')}"
            )
        place_text = " / ".join(place_strings)

        cleaned_events.append(
            {
                "ID": event.get("ID"),
                "카메라": event.get("CAMERA_ID"),
                "시간": event.get("REG_DATE"),
                "장소": place_text,
                "대상": event.get("TARGET_ID"),
            }
        )

    data_frame = pd.DataFrame(cleaned_events)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data_frame.to_excel(writer, index=False, sheet_name="Event_Logs")
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="event_logs.xlsx",
    )
