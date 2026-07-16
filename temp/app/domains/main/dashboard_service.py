from datetime import datetime

from app import configs
from app.domains.map.map import get_map_data
from app.utils.json_manager import (
    ACCOUNT_FILE,
    EVENT_LOGS_FILE,
    TARGETS_PROFILES_FILE,
    load_json,
)


DATE_FORMATS = (
    "%Y/%m/%d, %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
)


def _parse_datetime(value):
    """JSON에 저장된 여러 날짜 형식을 안전하게 datetime으로 변환한다."""
    if not value:
        return None

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except (TypeError, ValueError):
            continue

    return None


def _format_location(event):
    latitude = event.get(configs.KEY_EVENT_LAT)
    longitude = event.get(configs.KEY_EVENT_LON)

    if latitude is None or longitude is None:
        return "위치 정보 없음"

    try:
        return f"{float(latitude):.5f}, {float(longitude):.5f}"
    except (TypeError, ValueError):
        return f"{latitude}, {longitude}"


def _make_recent_events(events, targets, limit=6):
    recent_events = []

    sorted_events = sorted(
        events.values(),
        key=lambda event: _parse_datetime(event.get(configs.KEY_EVENT_DATE))
        or datetime.min,
        reverse=True,
    )

    for event in sorted_events[:limit]:
        target_id = event.get(configs.KEY_TARGET_ID, "-")
        target = targets.get(target_id, {})
        event_datetime = _parse_datetime(event.get(configs.KEY_EVENT_DATE))

        recent_events.append(
            {
                "id": event.get(configs.KEY_EVENT_ID, ""),
                "target_id": target_id,
                "target_name": target.get(configs.KEY_NAME, "미등록 대상"),
                "short_description": target.get(configs.KEY_SHORT_DESC, "탐지 이벤트"),
                "date": (
                    event_datetime.strftime("%Y.%m.%d %H:%M")
                    if event_datetime
                    else event.get(configs.KEY_EVENT_DATE, "-")
                ),
                "location": _format_location(event),
                "is_read": bool(event.get(configs.KEY_IS_READ, False)),
                "image": event.get(configs.KEY_EVENT_IMG_ROOT),
            }
        )

    return recent_events


def _get_camera_data():
    """현재 실행 중인 카메라 정보를 대시보드용으로 정리한다."""
    try:
        from app.domains.stream import camera as camera_manager

        camera_ids = list(camera_manager.get_all_camera_ids())
    except Exception:
        # AI/카메라 모듈이 아직 준비되지 않아도 대시보드는 정상 출력한다.
        camera_ids = []

    return {
        "camera_ids": camera_ids,
        "camera_count": len(camera_ids),
        "primary_camera_id": camera_ids[0] if camera_ids else None,
    }


def get_dashboard_data():
    accounts = load_json(ACCOUNT_FILE)
    events = load_json(EVENT_LOGS_FILE)
    targets = load_json(TARGETS_PROFILES_FILE)

    approved_users = sum(
        1
        for account in accounts.values()
        if account.get(configs.KEY_IS_APPROVE, False)
    )
    pending_users = max(0, len(accounts) - approved_users)
    unread_events = sum(
        1
        for event in events.values()
        if not event.get(configs.KEY_IS_READ, False)
    )

    camera_data = _get_camera_data()

    return {
        **camera_data,
        "stats": {
            "target_count": len(targets),
            "unread_event_count": unread_events,
            "approved_user_count": approved_users,
            "pending_user_count": pending_users,
            "user_count": len(accounts),
        },
        "recent_events": _make_recent_events(events, targets),
        "map_data": get_map_data(),
        "generated_at": datetime.now().strftime("%Y.%m.%d %H:%M"),
    }
