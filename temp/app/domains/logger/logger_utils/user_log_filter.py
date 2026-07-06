from app import configs


def filter_keyword(logs, keyword, tag):

    if not keyword:
        return logs

    keyword = keyword.lower()

    result = []

    for log in logs:

        if tag == "이벤트ID":
            value = str(
                log.get(configs.KEY_EVENT_LOG_ID, "")
            ).lower()

        elif tag == "확인자":
            value = str(
                log.get(configs.KEY_VIEWER_ID, "")
            ).lower()

        elif tag == "확인시간":
            value = str(
                log.get(configs.KEY_READ_DATE, "")
            ).lower()

        else:
            value = " ".join([
                str(log.get(configs.KEY_EVENT_LOG_ID, "")),
                str(log.get(configs.KEY_VIEWER_ID, "")),
                str(log.get(configs.KEY_READ_DATE, ""))
            ]).lower()

        if keyword in value:
            result.append(log)

    return result


def sort_logs(logs, sort):

    if sort == "최신순":
        return sorted(
            logs,
            key=lambda x: x.get(configs.KEY_READ_DATE, "")
        )

    if sort == "이벤트ID순":
        return sorted(
            logs,
            key=lambda x: x.get(configs.KEY_EVENT_LOG_ID, "")
        )

    return sorted(
        logs,
        key=lambda x: x.get(configs.KEY_READ_DATE, ""),
        reverse=True
    )