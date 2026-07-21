from app.configs import (KEY_EVENT_ID, 
    KEY_EVENT_DATE, KEY_TARGET_ID, KEY_IS_READ)


# ===========================================================
# 이벤트 로그 리스트의 필터에서 태그를 설정하고, 키워드를 검색 
# ===========================================================
def filter_keyword(logs, keyword, tag):

    if not keyword:
        return logs

    keyword = keyword.lower()

    result = []

    for log in logs:

        if tag == "이벤트ID":
            value = str(
                log.get(KEY_EVENT_ID, "")
            ).lower()

        elif tag == "대상ID":
            value = str(
                log.get(KEY_TARGET_ID, "")
            ).lower()

        elif tag == "발생시간":
            value = str(
                log.get(KEY_EVENT_DATE, "")
            ).lower()

        else:
            value = " ".join([
                str(log.get(KEY_EVENT_ID, "")),
                str(log.get(KEY_TARGET_ID, "")),
                str(log.get(KEY_EVENT_DATE, ""))
            ]).lower()

        if keyword in value:
            result.append(log)

    return result


# ===========================================================
# 이벤트 로그 리스트에서 '읽음'과 '읽지않음'상태 구분
# ===========================================================
def filter_status(events, status):

    if status == "전체":
        return events

    if status == "읽음":
        return [
            event
            for event in events
            if event.get(KEY_IS_READ)
        ]

    if status == "읽지않음":
        return [
            event
            for event in events
            if not event.get(KEY_IS_READ)
        ]

    return events


# ===========================================================
# 이벤트 로그 리스트의 데이터 나열 순서: 오래된순 vs 최신순 / 이벤트ID순
# ===========================================================
def sort_logs(logs, sort):

    if sort == "오래된순":
        return sorted(
            logs,
            key=lambda x: x.get(KEY_EVENT_DATE, "")
        )

    if sort == "이벤트ID순":
        return sorted(
            logs,
            key=lambda x: x.get(KEY_EVENT_ID, "")
        )

    return sorted(
        logs,
        key=lambda x: x.get(KEY_EVENT_DATE, ""),
        reverse=True
    )