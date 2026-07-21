from app.utils.time_stamper import get_current_time_stamp_formated
from app.utils.json_manager import (load_json, save_json, EVENT_LOGS_FILE)
from app.domains.logger.logger_utils.event_notifier import notify_new_log
from app.domains.logger.user_logs.user_logs import add_user_log
from app.configs import (KEY_EVENT_ID, 
    KEY_EVENT_DATE, KEY_EVENT_LAT, KEY_EVENT_LON, 
    KEY_TARGET_ID, KEY_IS_READ, KEY_EVENT_IMG_ROOT)
from uuid import uuid4
import logging


# ===========================================================
# - 이벤트 로그 전체를 가져와서 조회하는 함수 -
# event_logs.json을 load_json으로 받음(= logs)
# 화면 리스트의 형태로 출력 되기 때문에, logs를 리스트로 받음(= events)
# events를 KEY_EVENT_DATE를 기준으로 내림차순(최신)으로 정렬하고, 반환함
# ===========================================================
def get_event_list():

    logs = load_json(EVENT_LOGS_FILE)

    events = list(logs.values())

    events.sort(key=lambda x: x[KEY_EVENT_DATE], reverse=True)

    return events


# ===========================================================
# - uuid를 생성해, 새로운 이벤트 아이디에 할당하는 함수 -
# 새로운 이벤트 아이디를 문자열uuid로 반환함
# ===========================================================
def create_event_id():

    return str(uuid4())


# ===========================================================
# - 새로운 이벤트 로그를 만들기 위해 데이터 전달받는 함수 -
# 매개변수(latitude, longitude, target_id, filename)를 외부에서 호출
# 이미지를 전달받을 때, 이미지의 이름도 같이 전달받음(= image_path)
# 전달받은 매개변수로 딕셔너리를 만들기 위해, add_event함수를 실행함
# ===========================================================
def create_event_data(latitude, longitude, target_id, filename):

    image_path = f"img/event_img/{filename}"

    data = {KEY_EVENT_LAT: latitude, 
            KEY_EVENT_LON: longitude, 
            KEY_TARGET_ID: target_id, 
            KEY_EVENT_IMG_ROOT: image_path}

    add_event(data)


# 이벤트 로그에 데이터 전송하는법---------------------------------
"""
from app.domains.logger.event_logs.event_logs import (
    create_event_data)

create_event_data(
    target_id="person009",
    latitude=36.35,
    longitude=127.38,
    filename="ferrari.jpg"
)
"""


# ===========================================================
# - 생성된 새로운 이벤트 로그를 저장하는 함수 -
# event_logs.json을 load_json으로 받음(= logs)
# create_event_id를 통해 새로운 uuid 이벤트 아이디를 생성함(=event_id)
# 새로운 이벤트 로그 추가, KEY_EVENT_DATE의 데이터를
# get_current_time_stamp_formated()를 통해 현재시각을 가져오고,
# KEY_IS_READ가 False상태로서 추가되고, 메모리에서 json파일로 실제 저장됨
# SSE로 서버에서 웹으로 알림(= notify_new_log())
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
        KEY_EVENT_IMG_ROOT: data[KEY_EVENT_IMG_ROOT]
    }
    try:
        save_json(EVENT_LOGS_FILE, logs)

    except Exception as e:
        logging.exception(e)
        raise

    logging.info("Target=%s", data[KEY_TARGET_ID])

    notify_new_log()


# ===========================================================
# - 마지막 로그 이후의 새로운 로그를 반환하는 함수 -
# 브라우저가 보내는 매개변수(after_id)를 받아서 그 이전까지를 저장함
# 생성된 로그들 중에서 오래된 로그부터 저장하기 위함
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
# - 엑셀 저장용으로 데이터를 변환하는 함수 -
# 영문 KEY값을 한글 KEY값으로 변환하는 역할을 수행함
# 엑셀로 저장하기 전에, 데이터를 깨끗이 하기 위해 청소함
# 매개변수(events)는 이벤트 로그 모드로서 인식하기 위함
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
# - 이벤트 로그를 읽음 처리하는 함수 -
# 매개변수(event_ids, viewer_id)를 받아서 '읽지않음(False)' 상태의 
# 로그를 '읽음(True)' 상태로 변경한 다음에 저장함
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