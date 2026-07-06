from flask import Blueprint, render_template, request, redirect
from app.utils.account_manager import load_accounts, save_accounts
from .service import make_member, update_member, delete_member
from .request_data import get_member_list_options, get_member_add_data, get_member_update_data
from app.utils.member_filter import filter_keyword, filter_permission, filter_approve
from app.utils.member_sort import sort_accounts
from app.utils.pagination import paginate

member_bp = Blueprint(
    "member", __name__, template_folder="templates", static_folder="static", static_url_path="/member/static"
)

@member_bp.route("/member/update/<member_id>", methods=["POST"])
def member_update(member_id):

    account_db = load_accounts()

    member_data = get_member_update_data(request)

    if member_id in account_db:
        update_member(account_db, member_id, member_data["permission"], member_data["approve"])
        save_accounts(account_db)

    return redirect("/member/list")

@member_bp.route("/member/list")
def member_list():

    account_db = load_accounts()

    accounts = list(account_db.values())

    options = get_member_list_options(request)

    # 검색
    accounts = filter_keyword(accounts, options["keyword"], options["tag"])
    accounts = filter_permission(accounts, options["permission"])
    accounts = filter_approve(accounts, options["approve"])

    # 정렬
    accounts = sort_accounts(accounts, options["sort"])

    # 페이지네이션
    accounts, total_pages = paginate(accounts, options["page"], options["per_page"])

    return render_template(
        "member_list.html",
        account_db=accounts,
        keyword=options["keyword"],
        tag=options["tag"],
        permission=options["permission"],
        approve=options["approve"],
        sort=options["sort"],
        per_page=options["per_page"],
        page=options["page"],
        total_pages=total_pages,
        edit_id=options["edit_id"],
        mode=options["mode"]
    )

@member_bp.route("/member/add", methods=["POST"])
def member_add():

    account_db = load_accounts()

    member_data = get_member_add_data(request)

    if member_data["id"] in account_db:
        return """
        <script>
            alert('이미 존재하는 아이디입니다.');
            history.back();
        </script>
        """

    account_db[member_data["id"]] = make_member(member_data)

    save_accounts(account_db)

    return redirect("/member/list")

@member_bp.route("/member/delete/<member_id>")
def member_delete(member_id):

    account_db = load_accounts()

    delete_member(account_db, member_id)
    save_accounts(account_db)

    return redirect("/member/list")