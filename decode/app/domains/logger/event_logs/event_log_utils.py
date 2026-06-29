from flask import send_file
import pandas as pd
import io


def format_events(events):
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
    return cleaned_events


def create_excel_file(cleaned_events):
    data_frame = pd.DataFrame(cleaned_events)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data_frame.to_excel(
            writer,
            index=False,
            sheet_name="Event_Logs"
        )

    output.seek(0)

    return output


def download_excel_file(output):
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="event_logs.xlsx",
    )