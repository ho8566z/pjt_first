import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ACCOUNT_FILE = os.path.join(BASE_DIR, "jsons", "accounts.json")
DELETED_ID_FILE = os.path.join(BASE_DIR, "jsons", "deleted_id.json")

EVENT_LOGS_FILE = os.path.join(BASE_DIR, "jsons", "event_logs.json")
USER_LOGS_FILE = os.path.join(BASE_DIR, "jsons", "user_logs.json")

FACES_ENCODINGS_FILE = os.path.join(BASE_DIR, "jsons", "face_encodings.json")
TARGETS_PROFILES_FILE = os.path.join(BASE_DIR, "jsons", "target_profiles.json")
MAPS_FILE = os.path.join(BASE_DIR, "jsons", "maps.json")

def load_json(file):
    try:
        with open(file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


def save_json(file, json_data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    accounts = load_json(DELETED_ID_FILE)
    print(accounts)
