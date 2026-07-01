from flask import Blueprint, render_template, request
from app.domains.logger.user_logs.user_logs import (
    get_user_log_list, add_user, checked_user_log, 
    get_checked_user_logs, checked_select_user_log, format_user_logs)
from app.domains.logger.logger_utils.log_utils import (
    create_excel_file, download_excel_file)


user_log_bp = Blueprint(
    "user_log",
    __name__,
    url_prefix="/user_log",
    template_folder="../templates",
    static_folder="../static"
)

@user_log_bp.route("/user_log_list")
def user_log_list():

    logs = get_user_log_list()

    return render_template(
        "user_log_list.html",
        logs = logs)


@user_log_bp.route("/export_user_data")
def export_user_data():

    logs = get_user_log_list()

    cleand_logs = format_user_logs(logs)

    output = create_excel_file(
        cleand_logs, 
        sheet_name="User_Logs")

    return download_excel_file(
        output, 
        "user_logs.xlsx")


@user_log_bp.route("/add_user_log", methods=["POST"])
def add_user_log():

    data = request.get_json()

    if not data:
        return {
            "result": "fail", 
            "message": "Invalid JSON data"
        }, 400

    add_user(data)

    return {"result": "success"}, 201


@user_log_bp.route("/check/<user_log_id>", methods=["POST"])
def check(user_log_id):

    checked_user_log(user_log_id)

    return {"result": "success"}, 200


@user_log_bp.route("/get_checked", methods=["POST"])
def get_checked():

    data = request.get_json()

    get_checked_user_logs(data["ids"])

    return {"result": "success"}, 200


@user_log_bp.route("/checked_all", methods=["POST"])
def checked_select():

    data = request.get_json()

    checked_select_user_log(data["ids"])

    return {"result": "success"}, 200
