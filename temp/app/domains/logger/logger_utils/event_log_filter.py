from app import configs


def filter_keyword(logs, keyword, tag):

    if not keyword:
        return logs

    keyword = keyword.lower()

    result = []

    for log in logs:

        if tag == "이벤트ID":
            value = str(
                log.get(configs.KEY_EVENT_ID, "")
            ).lower()

        elif tag == "대상ID":
            value = str(
                log.get(configs.KEY_TARGET_ID, "")
            ).lower()

        elif tag == "발생시간":
            value = str(
                log.get(configs.KEY_EVENT_DATE, "")
            ).lower()

        else:
            value = " ".join([
                str(log.get(configs.KEY_EVENT_ID, "")),
                str(log.get(configs.KEY_TARGET_ID, "")),
                str(log.get(configs.KEY_EVENT_DATE, ""))
            ]).lower()

        if keyword in value:
            result.append(log)

    return result


def filter_status(events, status):

    if status == "전체":
        return events

    if status == "읽음":
        return [
            event
            for event in events
            if event.get(configs.KEY_IS_READ)
        ]

    if status == "읽지않음":
        return [
            event
            for event in events
            if not event.get(configs.KEY_IS_READ)
        ]

    return events


def sort_logs(logs, sort):

    if sort == "오래된순":
        return sorted(
            logs,
            key=lambda x: x.get(configs.KEY_EVENT_DATE, "")
        )

    if sort == "이벤트ID순":
        return sorted(
            logs,
            key=lambda x: x.get(configs.KEY_EVENT_ID, "")
        )

    return sorted(
        logs,
        key=lambda x: x.get(configs.KEY_EVENT_DATE, ""),
        reverse=True
    )