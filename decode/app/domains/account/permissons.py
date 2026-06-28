from enum import IntEnum, auto
from app.utils import json_manager


# 관련성 있는 권한은 백의 자릿수를 통일
# auto()는 이전에 선언된 상수에서 +1

# FIXME: thread safe, lambda사용. json_manager에서 조회, 수정을 진행하게 해야할듯

KEY_PERMISSIONS = "PERMISSIONS"
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
def apply_permissions(id, *permission: PERMISSON):
    # 마스터 계정 예외처리
    accounts = json_manager.load_json(json_manager.ACCOUNT_FILE)
    target_account = accounts[id]

    for perm in permission:
        target_account[KEY_PERMISSIONS].remove(perm)

    json_manager.save_json(json_manager.ACCOUNT_FILE, accounts)


# 권한 삭제 ======
def remove_permissions(id, *permission: PERMISSON):
    # 마스터 계정 예외처리
    accounts = json_manager.load_json(json_manager.ACCOUNT_FILE)
    target_account = accounts[id]

    for perm in permission:
        target_account[KEY_PERMISSIONS].remove(perm)

    json_manager.save_json(json_manager.ACCOUNT_FILE, accounts)


# 권한 조회 ======
def has_permissions(id, *permissions: PERMISSON):
    accounts = json_manager.load_json(json_manager.ACCOUNT_FILE)
    target_account = accounts[id]

    for perm in permissions:
        if perm in target_account[KEY_PERMISSIONS]:
            return True

    return False
