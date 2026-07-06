# ===========================================================================
# 계정 관리 서비스(account_service)
#
# 계정(Account) 생성 및 관리 기능을 담당하는 서비스 모듈
#
# 담당 기능
# - 회원가입 처리
# - 계정 생성 및 저장
# - 정보 수정 승인
# - 계정 삭제
# ===========================================================================


# 계정 Repository (JSON 저장/로드)
from app.domains.account.repository.account_repository import (
    save_accounts,       # 계정 전체 저장
    load_deleted_ids,    # 삭제된 ID 목록 로드
    save_deleted_ids,    # 삭제된 ID 목록 저장
)

# 현재 날짜/시간 생성 유틸
from app.utils.time_stamper import get_current_time_stamp_formated

# 전역 설정값 (KEY_* 상수)
from app import configs

# 회원가입 검증 함수
from app.domains.account.validate.validate import (
    is_id_exists,        # 아이디 존재 여부 확인
    validate_register    # 회원가입 전체 검증
)


# ==========================================================
# 계정 생성 (Factory 역할)
#
# 계정 데이터를 "만드는 역할만" 담당
# ==========================================================
def build_account(name, id, pw, email, phone):

    # 계정 데이터 구조 생성
    return {

        # 사용자 이름
        configs.KEY_NAME: name,

        # 로그인 ID
        configs.KEY_ID: id,

        # 비밀번호
        configs.KEY_PW: pw,

        # 이메일
        configs.KEY_EMAIL: email,

        # 전화번호
        configs.KEY_PHONE: phone,

        # 계정 생성 날짜
        configs.KEY_REG_DATE: get_current_time_stamp_formated(),

        # 마지막 수정 날짜
        configs.KEY_MOT_DATE: get_current_time_stamp_formated(),

        # 관리자 승인 여부 (기본: 미승인)
        configs.KEY_IS_APPROVE: False,

        # 최초 로그인 여부 (기본: True)
        configs.KEY_IS_FIRST_LOGIN: True,

        # 권한 목록
        configs.KEY_PERMISSIONS: [],

        # 상급 관리자 ID
        configs.KEY_SENIOR_ID: "master",
    }


# ==========================================================
# 회원가입 처리
#
# 1. 검증
# 2. 계정 생성
# 3. 저장
# ==========================================================
def register_user(accounts, name, id, pw, email, p1, p2, p3):

    # ------------------------------------------------------
    # 1. 회원가입 입력값 검증
    # ------------------------------------------------------
    success, message, phone = validate_register(
        accounts,
        id,
        pw,
        email,
        p1,
        p2,
        p3
    )

    # 검증 실패 시 종료
    if not success:
        return False, message

    # ------------------------------------------------------
    # 2. 계정 데이터 생성 (Factory 사용)
    # ------------------------------------------------------
    account = build_account(name, id, pw, email, phone)

    # 계정 추가
    accounts[id] = account

    # ------------------------------------------------------
    # 3. 계정 저장 (JSON)
    # ------------------------------------------------------
    save_accounts(accounts)

    return True, "회원가입이 완료되었습니다."


# ==========================================================
# 정보 수정 승인 (관리자 기능)
#
# 수정 요청 데이터를 실제 계정에 반영
# ==========================================================
def approve_update(accounts, id):

    # 수정 요청 존재 여부 확인
    if "REQUEST_UPDATE" not in accounts[id]:
        return False, "수정 요청이 없습니다."

    # 요청 데이터 가져오기
    request = accounts[id]["REQUEST_UPDATE"]

    # 실제 계정 데이터에 반영
    accounts[id][configs.KEY_PW] = request[configs.KEY_PW]
    accounts[id][configs.KEY_EMAIL] = request[configs.KEY_EMAIL]
    accounts[id][configs.KEY_PHONE] = request[configs.KEY_PHONE]

    # 요청 데이터 삭제
    del accounts[id]["REQUEST_UPDATE"]

    # 저장
    save_accounts(accounts)

    return True, "정보 수정이 완료되었습니다."


# ==========================================================
# 계정 삭제
#
# 계정 삭제 + 삭제 ID 기록 (재사용 방지)
# ==========================================================
def delete_account(accounts, id):

    # 존재 여부 확인
    if not is_id_exists(accounts, id):
        return False, "존재하지 않는 계정입니다."

    # 삭제 ID 목록 로드
    deleted_ids = load_deleted_ids()

    # 없으면 추가
    if id not in deleted_ids:
        deleted_ids.append(id)

    # 삭제 목록 저장
    save_deleted_ids(deleted_ids)

    # 계정 삭제
    del accounts[id]

    # 저장
    save_accounts(accounts)

    return True, "계정이 삭제되었습니다."