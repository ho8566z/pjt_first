from utils.time_stamper import get_current_time_stamp_formated
from utils import json_manager
import string
import delete_config
import config


def load_accounts():
    return json_manager.load_json(json_manager.ACCOUNT_FILE)


def save_accounts(accounts):
    return json_manager.save_json(json_manager.ACCOUNT_FILE, accounts)


"""
ACNT-003
ID 유효성 검사	ID는 반드시 유일한 값이어야만 하며 수정 불가능
"""


# 아이디 있는지
def is_id_exists(accounts, id):
    return id in accounts


# 입력한 비밀번호가 맞는지?
def is_pw_correct(accounts, id, pw):
    return is_id_exists(accounts, id) and accounts[id][config.KEY_PW] == pw


# 승인 상태가 어떤지?
def is_account_approve(accounts, id):
    return accounts[id][config.KEY_IS_APPROVE]


# 삭제된 아이디 목록 불러오기
def load_deleted_ids():
    return json_manager.load_json(delete_config.DELETED_ID_FILE)


# 삭제된 아이디 목록 저장하기
def save_deleted_ids(deleted_ids):
    json_manager.save_json(delete_config.DELETED_ID_FILE, deleted_ids)


"""
#ACNT-004
#PW 유효성 검사	PW는 8자 이상, 특수문자 1개 이상을 포함하며 수정 가능
# 8같은 숫자 password_length_limit 같은 뭐 상수로 빼기
"""


def is_password_valid(pw):

    if len(pw) < 8:
        return False

    special_chars = string.punctuation

    has_special = False

    for ch in pw:
        if ch in special_chars:
            has_special = True
            break

    if not has_special:
        return False
    return True


"""
ACNT-005	
EMAIL 유효성 검사
"@"포함, gmail, naver, daum등 미리 허용한 이메일 주소만 허용
"""


def is_email_valid(email):

    if "@" not in email:
        return False

    allow_domains = ["gmail.com", "naver.com", "daum.net"]

    domain = email.split("@")[1]

    if domain not in allow_domains:
        return False

    return True


"""
ACNT-006	
전화번호 유효성 검사	
"숫자로만 입력, 입력 칸을 3개로 나누어 하이픈 없이 입력하게 하며 하이픈 입력시 삭제하여 저장"
"""


def is_phone_vaild(p1, p2, p3):

    p1 = p1.replace("-", "").strip()
    p2 = p2.replace("-", "").strip()
    p3 = p3.replace("-", "").strip()

    if not (p1.isdigit() and p2.isdiigit() and p3.isdigit()):
        return False, "숫자만 입력 가능합니다."

    if len(p1) != 3 or len(p2) != 4 or len(p3) != 4:
        return False, "전화번호 형식이 올바르지 않습니다."

    full_phone = p1 + p2 + p3

    return True, full_phone


"""
ACNT-007	
계정 생성	계정 생성시 각 데이터 유효성 검사, 가입 직후 미승인 상태	
"""


def create_account(accounts, id, pw, email, phone):

    if is_id_exists(accounts, id):
        return False, "이미 존재하는 아이디입니다."

    deleted_ids = load_deleted_ids()

    if id in deleted_ids:
        return False, "삭제된 ID는 사용할 수 없습니다."

    if not is_password_valid(pw):
        return False, "비밀번호는 8자 이상이며 특수문자를 포함해야 합니다."

    if not is_email_valid(email):
        return False, "올바른 이메일 형식이 아닙니다."

    if not is_phone_vaild(phone):
        return False, "전화번호 형식이 올바르지 않습니다."

    accounts[id] = {
        config.KEY_ID: id,
        config.KEY_PW: pw,
        config.KEY_EMAIL: email,
        config.KEY_PHONE: phone,
        config.KEY_REG_DATE: get_current_time_stamp_formated(),
        config.KEY_MOT_DATE: get_current_time_stamp_formated(),
        config.KEY_IS_APPROVE: False,
        config.KEY_PERMISSIONS: [],
        config.KEY_SENIOR_ID: "master",
    }

    save_accounts(accounts)

    return True, "회원가입이 완료되었습니다."


"""
ACNT-008	
로그인	DB에 등록된 계정 정보를 조회하여 일치하는지 확인
"""


def login(id, pw):

    accounts = load_accounts()

    if not is_id_exists(accounts, id):
        return False, "존재하지 않는 아이디입니다."

    if not is_pw_correct(accounts, id, pw):
        return False, "비밀번호가 틀렸습니다."

    if not is_account_approve(accounts, id):
        return False, "관리자 승인 대기 중입니다."

    return True, "로그인 성공"


"""
ACNT-009	
정보 수정	상급 계정에 수정 요청.	
"변경이 불가능한 ID로 신원 조회를 한다면 계정 프로필이 수정되어도 문제 없을 가능성이 높음
다만 
"""


def approve_update(accounts, id):

    if "REQUEST_UPDATE" not in accounts[id]:
        return False, "수정 요청이 없습니다."

    request = accounts[id]["REQUEST_UPDATE"]

    accounts[id][config.KEY_PW] = request[config.KEY_PW]
    accounts[id][config.KEY_EMAIL] = request[config.KEY_EMAIL]
    accounts[id][config.KEY_PHONE] = request[config.KEY_PHONE]

    del accounts[id]["REQUEST_UPDATE"]

    save_accounts(accounts)

    return True, "정보 수정이 완료되었습니다."


# 이 경우 삭제된 ID도 모두 기록해 재활용 불가능하게 해야함.
def delete_account(accounts, id):

    if not is_id_exists(accounts, id):
        return False, "존재하지 않는 계정입니다."

    deleted_ids = load_deleted_ids()

    if id not in deleted_ids:
        deleted_ids.append(id)

    save_deleted_ids(deleted_ids)

    del accounts[id]

    save_accounts(accounts)

    return True, "계정이 삭제되었습니다."
