from app.utils.json_manager import (ACCOUNT_FILE, load_json, save_json)

def load_accounts():
    return load_json(ACCOUNT_FILE)

def save_accounts(account_db):
    save_json(ACCOUNT_FILE, account_db)
