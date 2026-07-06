# ===========================================================================
# 검증 모듈(validate)
#
# 계정 정보에 대한 유효성(Validation) 검사를 담당하는 모듈
# ===========================================================================

from app import configs
import string

# ==========================================================
# 아이디 존재 여부 확인
# ==========================================================
def is_id_exists(accounts, id):
    return id in accounts


# ==========================================================
# 계정 승인 여부 확인
# ==========================================================
def is_account_approve(accounts, id):
    return accounts[id][configs.KEY_IS_APPROVE]


# ==========================================================
# 비밀번호 일치 여부 확인
# ==========================================================
def is_pw_correct(accounts, id, pw):
    return (
        is_id_exists(accounts, id)
        and accounts[id][configs.KEY_PW] == pw
    )


# ==========================================================
# 비밀번호 규칙 검사
# ==========================================================
def is_password_valid(pw):

    # 최소 길이 검사
    if len(pw) < configs.PASSWORD_MIN_LENGTH:
        return False

    # 특수문자 포함 여부 검사
    for ch in pw:
        if ch in string.punctuation:
            return True

    return False


# ==========================================================
# 이메일 형식 검사
# ==========================================================
def is_email_valid(email):

    # @ 포함 여부 체크
    if "@" not in email:
        return False

    # 도메인 추출
    domain = email.split("@")[1]

    # 허용 도메인 검사
    if domain not in configs.ALLOW_EMAIL_DOMAINS:
        return False

    return True


# ==========================================================
# 전화번호 유효성 검사
# ==========================================================
def is_phone_valid(p1, p2, p3):

    # 하이픈 제거 및 공백 제거
    p1 = p1.replace("-", "").strip()
    p2 = p2.replace("-", "").strip()
    p3 = p3.replace("-", "").strip()

    # 숫자 여부 검사
    if not (p1.isdigit() and p2.isdigit() and p3.isdigit()):
        return False, "숫자만 입력 가능합니다."

    # 자리수 검사
    if len(p1) != 3 or len(p2) != 4 or len(p3) != 4:
        return False, "전화번호 형식이 올바르지 않습니다."

    # 최종 조합
    full_phone = p1 + p2 + p3

    return True, full_phone


# ==========================================================
# 비밀번호 변경 검증
# ==========================================================
def validate_change_password(accounts, id, oPw, nPw, new_pw_check):

    # 1. 아이디 존재 확인
    if not is_id_exists(accounts, id):
        return False, "없는 회원입니다."

    # 2. 현재 비밀번호 확인
    if accounts[id][configs.KEY_PW] != oPw:
        return False, "현재 임시 비밀번호가 일치하지 않습니다."

    # 3. 새 비밀번호 확인
    if nPw != new_pw_check:
        return False, "새 비밀번호가 서로 일치하지 않습니다."

    # 4. 비밀번호 규칙 검사
    if not is_password_valid(nPw):
        return False, "비밀번호는 8자 이상이며 특수문자를 포함해야 합니다."

    # 5. 기존 비밀번호 동일 여부
    if oPw == nPw:
        return False, "기존 비밀번호와 다르게 설정해야 합니다."

    return True, None


# ==========================================================
# 회원가입 검증
# ==========================================================
def validate_register(accounts, id, pw, email, p1, p2, p3):

    # 1. 아이디 중복 검사
    if is_id_exists(accounts, id):
        return False, "이미 존재하는 아이디입니다.", None

    # 2. 삭제된 아이디 검사
    from app.domains.account.repository.account_repository import load_deleted_ids
    deleted_ids = load_deleted_ids()

    if id in deleted_ids:
        return False, "삭제된 ID는 사용할 수 없습니다.", None

    # 3. 비밀번호 검사
    if not is_password_valid(pw):
        return False, "비밀번호는 8자 이상이며 특수문자를 포함해야 합니다.", None

    # 4. 이메일 검사
    if not is_email_valid(email):
        return False, "올바른 이메일 형식이 아닙니다.", None

    # 5. 전화번호 검사 + 변환
    success, phone = is_phone_valid(p1, p2, p3)

    if not success:
        return False, phone, None

    # 최종 성공
    return True, None, phone