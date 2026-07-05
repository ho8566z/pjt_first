from flask import Blueprint, render_template, url_for, request
from app.domains.logger.user_logs.user_logs import (
    get_user_log_list, format_user_logs)
from app.domains.logger.logger_utils.log_utils import (
    create_excel_file, download_excel_file)
from app.utils.pagination import paginate


user_log_bp = Blueprint(
    "user_log",
    __name__,
    url_prefix="/user_log",
    template_folder="../templates",
    static_folder="../static"
)

@user_log_bp.route("/log_list_user")
def user_log_list():

    logs = get_user_log_list()

    per_page = request.args.get("per_page", default=10, type=int)
    page = request.args.get("page", default=1, type=int)

    logs, total_pages = paginate(
        logs,
        page,
        per_page)

    return render_template(
        "log_list_user.html",
        logs = logs,
        per_page = per_page,
        page = page,
        total_pages = total_pages,
        title = "사용자 로그",
        description = "사용자의 로그 확인 내역",
        mode = "user",
        download_url = url_for("user_log.export_user_data")
    )


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