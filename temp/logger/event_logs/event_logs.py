from app.utils.time_stamper import (
    get_current_time_stamp_formated)
from app.utils.json_manager import (
    load_json, save_json, EVENT_LOGS_FILE, 
    TARGETS_PROFILES_FILE)


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
        "TARGET_ID": data["TARGET_ID"]
    }

    save_json(EVENT_LOGS_FILE, logs)


def format_events(events):
    targets = load_json(TARGETS_PROFILES_FILE)

    cleaned_events = []

    for event in events:
        target_id = event.get("TARGET_ID")

        # if target_id not in targets:
        #     continue

        place_text = f"{event.get('latitude')}, {event.get('longitude')}"
            
        cleaned_events.append(
            {
                "ID": event.get("ID"),
                "시간": event.get("REG_DATE"),
                "장소": place_text,
                "대상ID": target_id
            }
        )
    return cleaned_events


if __name__ == "__main__":
    events = get_event_list()

    for event in events:
        print(event)
