from app.utils.time_stamper import get_current_time_stamp_formated
from app import configs
from app.utils.account_manager import load_accounts
from flask import session   
from app.domains.account.permissions import PERMISSON
from app.domains.account.permissions import ADMIN, OBSERVER

# ==========================================================
# 회원 정보 생성
# ==========================================================
def make_member(member_data):

    # 회원 생성 시간
    now = get_current_time_stamp_formated()

    # 선택한 역할에 따라 권한 목록 생성
    if member_data["permission"] == "ADMIN":
        permissions = [perm.value for perm in ADMIN]
    else:
        permissions = [perm.value for perm in OBSERVER]

    # 회원 정보 생성
    return {
        configs.KEY_ID: member_data["id"],
        configs.KEY_PW: member_data["pw"],
        configs.KEY_NAME: member_data["name"],
        configs.KEY_PHONE: member_data["phone"],
        configs.KEY_EMAIL: member_data["email"],
        configs.KEY_PERMISSIONS: permissions,
        configs.KEY_IS_APPROVE: member_data["approve"] == "승인",
        configs.KEY_IS_FIRST_LOGIN: True,
        configs.KEY_REG_DATE: now,
        configs.KEY_MOD_DATE: now
    }


# ==========================================================
# 회원 정보 수정
# ==========================================================
def update_member(account_db, member_id, permission, approve):

    # 관리자 권한 확인
    if not is_admin(session["id"]):
        return False, "권한이 없습니다."

    # 선택한 역할에 따라 권한 변경
    if permission == "ADMIN":
        account_db[member_id][configs.KEY_PERMISSIONS] = [
            perm.value for perm in ADMIN
        ]
    else:
        account_db[member_id][configs.KEY_PERMISSIONS] = [
            perm.value for perm in OBSERVER
        ]

    # 승인 상태 변경
    account_db[member_id][configs.KEY_IS_APPROVE] = (
        approve == "승인"
    )

    # 수정 시간 갱신
    account_db[member_id][configs.KEY_MOD_DATE] = (
        get_current_time_stamp_formated()
    )

    return True, "수정 완료"


# ==========================================================
# 회원 삭제
# ==========================================================
def delete_member(account_db, member_id):

    # 회원이 존재하면 삭제
    if member_id in account_db:
        del account_db[member_id]


# ==========================================================
# 회원 관리 권한 보유 여부 확인
# ==========================================================
def is_admin(user_id):

    # 계정 정보 로드
    accounts = load_accounts()

    # 회원 관리 권한(MEMBER_ACCESS) 보유 여부 확인
    return (
        PERMISSON.MEMBER_ACCESS.value
        in accounts[user_id][configs.KEY_PERMISSIONS]
    )