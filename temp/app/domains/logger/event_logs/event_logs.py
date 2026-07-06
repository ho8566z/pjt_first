from app.utils.time_stamper import (
    get_current_time_stamp_formated)
from app.utils.json_manager import (
    load_json, save_json, EVENT_LOGS_FILE, 
    USER_LOGS_FILE)


def get_event_list():

    logs = load_json(EVENT_LOGS_FILE)

    return list(logs.values())


def add_event(data):

    logs = load_json(EVENT_LOGS_FILE)

    logs[data["ID"]] = {
        "ID": data["ID"],
        "REG_DATE": get_current_time_stamp_formated(),
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "TARGET_ID": data["TARGET_ID"],
        "IS_READ": False
    }

    save_json(EVENT_LOGS_FILE, logs)


def format_events(events):

    cleaned_events = []

    for event in events:
        cleaned_events.append(
            {
                "이벤트_ID": event.get("ID"),
                "이벤트_발생시각": event.get("REG_DATE"),
                "이벤트_발생위도": event.get("latitude"),
                "이벤트_발생경도": event.get("longitude"),
                "대상_ID": event.get("TARGET_ID"),
                "이벤트_상태": event.get("IS_READ")
            }
        )
    return cleaned_events


def checked_event_logs(event_ids, viewer_id):

    events = load_json(EVENT_LOGS_FILE)
    users = load_json(USER_LOGS_FILE)

    for event_id in event_ids:

        if event_id not in events:
            continue

        if events[event_id]["IS_READ"]:
            continue

        events[event_id]["IS_READ"] = True

        read_date = get_current_time_stamp_formated()

        user_id = f"user_{len(users)+1:03d}"

        users[user_id] = {
            "EVENT_LOG_ID": event_id,
            "VIEWER_ID": viewer_id,
            "READ_DATE": read_date
        }

    save_json(EVENT_LOGS_FILE, events)
    save_json(USER_LOGS_FILE, users)


if __name__ == "__main__":
    events = get_event_list()

    for event in events:
        print(event)