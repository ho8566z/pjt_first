from app.utils.json_manager import (
    load_json, save_json, USER_LOGS_FILE)
from app.utils.time_stamper import (
    get_current_time_stamp_formated)
from app.configs import (
    KEY_LOG_ID, KEY_EVENT_LOG_ID, 
    KEY_VIEWER_ID, KEY_READ_DATE)


# ===========================================================
# 사용자 로그 저장
# ===========================================================
def add_user_log(event_id, viewer_id):

    users = load_json(USER_LOGS_FILE)

    user_id = f"user_{len(users)+1:03d}"

    users[user_id] = {

        KEY_EVENT_LOG_ID: event_id,
        KEY_VIEWER_ID: viewer_id,
        KEY_READ_DATE: get_current_time_stamp_formated()
    }

    save_json(USER_LOGS_FILE, users)


# ===========================================================
# 사용자 로그 전체 조회
# ===========================================================
def get_user_log_list():

    logs = load_json(USER_LOGS_FILE)

    result = []

    for key, value in logs.items():

        log = value.copy()
        log[KEY_LOG_ID] = key

        result.append(log)

    return result


# ===========================================================
# 엑셀 저장용 데이터 변환
# ===========================================================
def format_user_logs(user_logs):
    cleaned_user_logs = []

    for user_log in user_logs:
        cleaned_user_logs.append(
            {
                "이벤트_ID": user_log.get(KEY_EVENT_LOG_ID),
                "확인자_ID": user_log.get(KEY_VIEWER_ID),
                "이벤트_확인시각": user_log.get(KEY_READ_DATE)
            }
        )

    return cleaned_user_logs



if __name__ == "__main__":
    user_logs = get_user_log_list()

    for user_log in user_logs:
        print(user_log)