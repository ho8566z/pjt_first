# ===========================================================================
# 인증 서비스(auth_service)
#
# 로그인(Authentication)과 관련된 모든 기능을 담당하는 서비스
# ===========================================================================

from app.domains.account.repository.account_repository import (
    load_accounts,
    save_accounts,
)

from app.utils.time_stamper import get_current_time_stamp_formated
from app import configs
from flask import session
from app.domains.account.permissions import PERMISSON

from app.domains.account.validate.validate import is_id_exists, validate_change_password


# ==========================================================
# 일반 로그인 검사 (기본 검증 로직)
# ==========================================================
def check_login(accounts, id, pw):

    # 아이디 존재 여부
    if not is_id_exists(accounts, id):
        return False, "없는 회원입니다.", None

    # 비밀번호 검증
    if accounts[id][configs.KEY_PW] != pw:
        return False, "비밀번호가 틀렸습니다.", None

    # 승인 대기 상태
    if not accounts[id][configs.KEY_IS_APPROVE]:
        return True, "pending", accounts[id]

    # 로그인 성공
    return True, "로그인 성공", accounts[id]


# ==========================================================
# CAPTCHA 검사
# ==========================================================
def check_captcha(captcha, accounts, id):

    # 로그인 실패 횟수 확인
    login_fail = session.get("login_fail", 0)

    # 실패가 기준 미만이면 CAPTCHA 검사 안함
    if login_fail < configs.LOGIN_FAIL_LIMIT:
        return True, None

    # CAPTCHA 실패 횟수
    captcha_fail = session.get("captcha_fail", 0)

    # CAPTCHA 불일치
    if captcha != session.get("captcha", ""):
        captcha_fail += 1
        session["captcha_fail"] = captcha_fail

        if captcha_fail >= configs.LOGIN_FAIL_LIMIT:
            if id in accounts:
                accounts[id][configs.KEY_IS_APPROVE] = False

            save_accounts(accounts)
            return False, "자동입력 방지를 3회 실패하여 계정이 비활성화되었습니다."

        return False, f"자동문자 입력이 틀렸습니다. ({captcha_fail}/3)"

    # CAPTCHA 성공
    return True, None


# ==========================================================
# 로그인 실패 횟수 초기화
# ==========================================================
def reset_login_fail():

    session["login_fail"] = 0
    session["captcha_fail"] = 0


# ==========================================================
# 로그인 실패 처리
# ==========================================================
def login_fail_session(message):

    login_fail = session.get("login_fail", 0)

    if login_fail < configs.LOGIN_FAIL_LIMIT:
        login_fail += 1
        session["login_fail"] = login_fail

    return login_fail, message


# ==========================================================
# 로그인 Session 생성
# ==========================================================
def create_login_session(user):

    session["id"] = user[configs.KEY_ID]
    session["is_approve"] = user[configs.KEY_IS_APPROVE]
    session["is_first_login"] = user[configs.KEY_IS_FIRST_LOGIN]
    session["permissions"] = user[configs.KEY_PERMISSIONS]

    # 사용자 권한명 저장
    if PERMISSON.MEMBER_ACCESS.value in user[configs.KEY_PERMISSIONS]:
        session["user_permission"] = "관리자"
    else:
        session["user_permission"] = "관제자"


# ==========================================================
# 로그인 처리 (메인 흐름)
# ==========================================================
def login(id, pw, captcha=""):

    # 공백 검사
    success, message = validate_login_input(id, pw)

    if not success:
        return False, message, None

    accounts = load_accounts()

    # CAPTCHA 먼저 검사
    captcha_success, captcha_message = check_captcha(captcha, accounts, id)

    # 로그인 검증
    login_success, login_message, user = check_login(accounts, id, pw)

    if not captcha_success:
        return False, captcha_message, None

    if not login_success:
        return False, login_message, None

    # 성공 시 실패 기록 초기화

    reset_login_fail()

    return True, login_message, user


# ==========================================================
# 최초 로그인 비밀번호 변경
# ==========================================================
def change_password(id, oPw, nPw, new_pw_check):

    accounts = load_accounts()

    # 비밀번호 변경 검증
    success, message = validate_change_password(accounts, id, oPw, nPw, new_pw_check)

    if not success:
        return False, message

    # 비밀번호 업데이트
    accounts[id][configs.KEY_PW] = nPw
    accounts[id][configs.KEY_IS_FIRST_LOGIN] = False
    accounts[id][configs.KEY_MOD_DATE] = get_current_time_stamp_formated()

    save_accounts(accounts)

    return True, "비밀번호가 변경되었습니다."


# ==========================================================
# 로그인 입력값 공백 검사
# ==========================================================
def validate_login_input(id, pw):

    # 아이디 입력 여부 확인
    if not id.strip():
        return False, "아이디를 입력하세요"

    # 비밀번호 입력 여부 확인
    if not pw.strip():
        return False, "비밀번호를 입력하세요"

    # 모든 입력값이 존재하면 성공
    return True, None
