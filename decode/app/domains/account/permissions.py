from enum import IntEnum, auto
from app.utils.json_manager import save_json, load_json, ACCOUNT_FILE
from app.configs import KEY_PERMISSIONS

# ==========================================================
# 권한 번호 규칙
# ==========================================================
# 관련 있는 권한은 백의 자릿수를 동일하게 사용
# ex)
# 100번대 : 서비스 화면 접근 권한
# 200번대 : 회원 관리 권한
# 300번대 : 로그 조회 권한
#
# auto()는 이전 값에서 +1씩 자동 증가
# 예)
# STREAM_ACCESS = 101
# PROFILE_ACCESS = 102


# ==========================================================
# 시스템 권한(Enum)
# ==========================================================
class PERMISSON(IntEnum):
    """서비스 접근 권한"""

    # 메인 기능 접근 권한
    DASHBOARD_ACCESS = 100
    STREAM_ACCESS = auto()
    PROFILE_ACCESS = auto()
    CAMERA_ACCESS = auto()

    # 회원 관리 권한
    MEMBER_ACCESS = 200

    # 로그 조회 권한
    EVENT_LOG_ACCESS = 300
    USER_LOG_ACCESS = auto()


# ==========================================================
# 관리자 권한 묶음
# ==========================================================
# 관리자 계정 생성 시 한 번에 부여할 권한 목록
ADMIN = (
    PERMISSON.DASHBOARD_ACCESS,
    PERMISSON.STREAM_ACCESS,
    PERMISSON.PROFILE_ACCESS,
    PERMISSON.CAMERA_ACCESS,
    PERMISSON.MEMBER_ACCESS,
    PERMISSON.EVENT_LOG_ACCESS,
    PERMISSON.USER_LOG_ACCESS,
)


# ==========================================================
# 관제 인원 권한 묶음
# ==========================================================
# 관제 담당자에게 필요한 최소 권한
OBSERVER = (
    PERMISSON.CAMERA_ACCESS,
    PERMISSON.EVENT_LOG_ACCESS,
)


# ==========================================================
# 권한 추가
# ==========================================================
def apply_permissions(id, *permissions: PERMISSON):
    """
    특정 계정에 권한을 추가한다.
    이미 보유한 권한은 중복 추가하지 않는다.
    """

    # 계정 정보 불러오기
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    # 권한 추가
    for perm in permissions:
        if not has_permissions(id, perm):
            target_account[KEY_PERMISSIONS].append(perm.value)

    # 변경사항 저장
    save_json(ACCOUNT_FILE, accounts)


# ==========================================================
# 권한 삭제
# ==========================================================
def remove_permissions(id, *permissions: PERMISSON):
    """
    특정 계정의 권한을 삭제한다.
    보유하지 않은 권한은 삭제를 시도하지 않는다.
    """

    # 계정 정보 불러오기
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    # 권한 제거
    for perm in permissions:

        # 권한이 없으면 건너뛴다.
        if not has_permissions(id, perm):
            continue

        target_account[KEY_PERMISSIONS].remove(perm.value)

    # 변경사항 저장
    save_json(ACCOUNT_FILE, accounts)


# ==========================================================
# 권한 보유 여부 확인
# ==========================================================
def has_permissions(id, *permissions: PERMISSON):
    """
    여러 권한을 전달하면
    모든 권한을 가지고 있을 때만 True를 반환한다.
    """

    # 계정 정보 불러오기
    accounts = load_json(ACCOUNT_FILE)
    target_account = accounts[id]

    possess_cnt = 0

    # 보유한 권한 개수 확인
    for perm in permissions:
        if perm.value in target_account[KEY_PERMISSIONS]:
            possess_cnt += 1

    # 전달받은 권한을 모두 보유하고 있는지 확인
    return possess_cnt == len(permissions)