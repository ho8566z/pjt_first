from app.utils.json_manager import load_json
from app.utils.json_manager import EVENT_LOGS_FILE


def get_event_list():

    logs = load_json(EVENT_LOGS_FILE)

    return list(logs.values())


if __name__ == "__main__":
    events = get_event_list()

    for event in events:
        print(event)
