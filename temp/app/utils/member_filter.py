from app import configs
from app.domains.account.permissions import PERMISSON


def get_permission_name(account):

    permission_name = account.get("PERMISSION_NAME")

    if permission_name:
        return str(permission_name)

    permissions = account.get(configs.KEY_PERMISSIONS, [])

    if PERMISSON.MEMBER_ACCESS.value in permissions:
        return "관리자"

    return "관제자"


def filter_keyword(accounts, keyword, tag):

    if not keyword:
        return accounts

    keyword = keyword.strip().lower()

    if tag == "아이디":
        return [account for account in accounts if keyword in str(account.get(configs.KEY_ID, "")).lower()]

    elif tag == "이름":
        return [account for account in accounts if keyword in str(account.get(configs.KEY_NAME, "")).lower()]

    elif tag == "역할":
        return [account for account in accounts if keyword in get_permission_name(account).lower()]

    # 태그가 전체인 경우
    return [account for account in accounts
        if (keyword in str(account.get(configs.KEY_ID, "")).lower()

            or keyword in str(account.get(configs.KEY_NAME, "")).lower()

            or keyword in get_permission_name(account).lower()
        )
    ]


def filter_permission(accounts, permission):

    if permission == "전체":
        return accounts

    return [account for account in accounts if get_permission_name(account) == permission]


def filter_approve(accounts, approve):

    if approve == "승인":
        return [account for account in accounts if account.get(configs.KEY_IS_APPROVE) is True]

    elif approve == "미승인":
        return [account for account in accounts if account.get(configs.KEY_IS_APPROVE) is False]

    return accounts