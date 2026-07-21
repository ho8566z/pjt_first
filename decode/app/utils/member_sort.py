from app import configs

def sort_accounts(accounts, sort):

    if sort == "최신등록순":
        accounts.sort(
            key=lambda a: a.get(configs.KEY_REG_DATE, ""),
            reverse=True
        )

    elif sort == "오래된순":
        accounts.sort(
            key=lambda a: a.get(configs.KEY_REG_DATE, "")
        )

    elif sort == "아이디순":
        accounts.sort(
            key=lambda a: a.get(configs.KEY_ID, "")
        )

    elif sort == "이름순":
        accounts.sort(
            key=lambda a: a.get(configs.KEY_NAME, "")
        )

    return accounts