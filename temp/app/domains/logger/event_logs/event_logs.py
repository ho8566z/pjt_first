from app.utils.time_stamper import get_current_time_stamp_formated
from app.utils.json_manager import load_json, save_json, EVENT_LOGS_FILE
from app.domains.logger.logger_utils.event_notifier import notify_new_log
from app.domains.logger.user_logs.user_logs import add_user_log
from app.configs import (KEY_EVENT_ID, KEY_EVENT_DATE,
    KEY_EVENT_LAT, KEY_EVENT_LON, KEY_TARGET_ID, KEY_IS_READ)
from uuid import uuid4
import logging


# ===========================================================
# 이벤트 로그 전체 조회
# ===========================================================
def get_event_list():

    logs = load_json(EVENT_LOGS_FILE)

    events = list(logs.values())

    events.sort(key=lambda x: x[KEY_EVENT_DATE], reverse=True)

    return events


# ===========================================================
# 새로운 이벤트 아이디 uuid로 입력
# ===========================================================
def create_event_id():

    return str(uuid4())


# ===========================================================
# 새로운 이벤트 데이터 불러오기
# ===========================================================
def create_event_data(latitude, longitude, target_id):
    data = {KEY_EVENT_LAT: latitude, KEY_EVENT_LON: longitude, KEY_TARGET_ID: target_id}

    add_event(data)


# 이벤트 로그에 데이터 전송하는법---------------------------------
"""
from app.domains.logger.event_logs.event_logs import (
    create_event_data)

create_event_data(
    target_id="target001",
    latitude=36.35,
    longitude=127.38
)
"""


# ===========================================================
# 새로운 이벤트 저장
# ===========================================================
def add_event(data):

    logs = load_json(EVENT_LOGS_FILE)
    event_id = create_event_id()

    logs[event_id] = {
        KEY_EVENT_ID: event_id,
        KEY_EVENT_DATE: get_current_time_stamp_formated(),
        KEY_EVENT_LAT: data[KEY_EVENT_LAT],
        KEY_EVENT_LON: data[KEY_EVENT_LON],
        KEY_TARGET_ID: data[KEY_TARGET_ID],
        KEY_IS_READ: False,
    }
    try:
        save_json(EVENT_LOGS_FILE, logs)

    except Exception as e:
        logging.exception(e)
        raise

    logging.info("Target=%s", data[KEY_TARGET_ID])

    notify_new_log()


# ===========================================================
# 마지막으로 받은 로그 이후의 로그 반환
# ===========================================================
def get_new_event_list(after_id):

    events = get_event_list()

    if after_id is None:
        return events

    new_events = []

    for event in events:
        if event[KEY_EVENT_ID] == after_id:
            break

        new_events.append(event)

    return list(reversed(new_events))


# ===========================================================
# 엑셀 저장용 데이터 변환
# ===========================================================
def format_events(events):

    cleaned_events = []

    for event in events:
        cleaned_events.append(
            {
                "이벤트_ID": event.get(KEY_EVENT_ID),
                "이벤트_발생시각": event.get(KEY_EVENT_DATE),
                "이벤트_발생위도": event.get(KEY_EVENT_LAT),
                "이벤트_발생경도": event.get(KEY_EVENT_LON),
                "대상_ID": event.get(KEY_TARGET_ID),
                "이벤트_상태": event.get(KEY_IS_READ),
            }
        )

    return cleaned_events


# ===========================================================
# 이벤트 읽음 처리
# ===========================================================
def checked_event_logs(event_ids, viewer_id):

    events = load_json(EVENT_LOGS_FILE)

    for event_id in event_ids:
        if event_id not in events:
            continue

        if events[event_id][KEY_IS_READ]:
            continue

        events[event_id][KEY_IS_READ] = True

        add_user_log(event_id, viewer_id)

    save_json(EVENT_LOGS_FILE, events)


if __name__ == "__main__":
    events = get_event_list()

    for event in events:
        print(event)