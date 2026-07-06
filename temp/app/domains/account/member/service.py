from app.utils.time_stamper import get_current_time_stamp_formated
from app import configs


def make_member(member_data):

    now = get_current_time_stamp_formated()

    return {
        configs.KEY_ID: member_data["id"],
        configs.KEY_PW: member_data["pw"],
        configs.KEY_NAME: member_data["name"],
        configs.KEY_PHONE: member_data["phone"],
        configs.KEY_EMAIL: member_data["email"],
        configs.KEY_PERMISSIONS: [member_data["permission"]],
        configs.KEY_IS_APPROVE: member_data["approve"] == "승인",
        configs.KEY_IS_FIRST_LOGIN: True,
        configs.KEY_REG_DATE: now,
        configs.KEY_MOT_DATE: now
    }


def update_member(account_db, member_id, permission, approve):

    account_db[member_id][configs.KEY_PERMISSIONS] = [permission]
    account_db[member_id][configs.KEY_IS_APPROVE] = approve == "승인"
    account_db[member_id][configs.KEY_MOT_DATE] = get_current_time_stamp_formated()


def delete_member(account_db, member_id):

    if member_id in account_db:
        del account_db[member_id]