import json
from app.utils.json_manager import ACCOUNT_FILE
from flask import Blueprint, render_template

member_bp = Blueprint(
    "member", __name__, template_folder="templates", static_folder="static"
)


@member_bp.route("/member/list")
def member_list():

    with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
        account_db = json.load(f)

    return render_template("member_list.html", account_db=account_db)
