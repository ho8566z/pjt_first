from app.utils.json_manager import (
    load_json, USER_LOGS_FILE)


def get_user_log_list():

    logs = load_json(USER_LOGS_FILE)

    result = []

    for key, value in logs.items():

        log = value.copy()
        log["ID"] = key

        result.append(log)

    return result


def format_user_logs(user_logs):
    cleaned_user_logs = []

    for user_log in user_logs:
        cleaned_user_logs.append(
            {
                "이벤트_ID": user_log.get("EVENT_LOG_ID"),
                "확인자_ID": user_log.get("VIEWER_ID"),
                "이벤트_확인시각": user_log.get("READ_DATE")
            }
        )

    return cleaned_user_logs


if __name__ == "__main__":
    user_logs = get_user_log_list()

    for user_log in user_logs:
        print(user_log)