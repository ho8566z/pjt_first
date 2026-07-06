from enum import IntEnum, auto
from app.utils.json_manager import save_json, load_json, ACCOUNT_FILE
from app.configs import KEY_PERMISSIONS

# 관련성 있는 권한은 백의 자릿수를 통일
# auto()는 이전에 선언된 상수에서 +1

# FIXME: thread safe, lambda사용. json_manager에서 조회, 수정을 진행하게 해야할듯

# permission_modify_lock = threading.Lock()


class PERMISSON(IntEnum):
    """서비스 접근 권한"""

    CREATE_ACCOUNT = 100
    UPDATE_ACCOUNT = auto()
    DELETE_ACCOUNT = auto()

    APPROVE_ACCOUNT = 200
    CAMERA_ACCESS = 300

    EVENT_LOG_ACCESS = 400
    USER_LOG_ACCESS = auto()


# 권한 추가 ======
def apply_permissions(id, *permissions: PERMISSON):
    """있는 권한은 추가하지 않음"""
    # 마스터 계정 예외처리
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    for perm in permissions:
        if not has_permissions(id, perm):
            target_account[KEY_PERMISSIONS].append(perm)

    save_json(ACCOUNT_FILE, accounts)


# 권한 삭제 ======
def remove_permissions(id, *permissions: PERMISSON):
    """없는 권한은 삭제를 시도하지 않음"""
    # 마스터 계정 예외처리
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    for perm in permissions:
        if not has_permissions(id, perm):
            continue

        target_account[KEY_PERMISSIONS].remove(perm)

    save_json(ACCOUNT_FILE, accounts)


# 권한 체크 ======
def has_permissions(id, *permissions: PERMISSON):
    """여러 개의 권한을 체크하는 경우, 모든 권한을 보유한 경우에만 true"""
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    possess_cnt = 0

    for perm in permissions:
        if perm in target_account[KEY_PERMISSIONS]:
            possess_cnt += 1

    return possess_cnt == len(permissions)
