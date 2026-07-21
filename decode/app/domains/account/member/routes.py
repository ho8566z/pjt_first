from flask import Blueprint, render_template, request, redirect, url_for, session
from app.utils.account_manager import load_accounts, save_accounts
from .service import make_member, update_member, delete_member, is_admin
from .request_data import (
    get_member_list_options,
    get_member_add_data,
    get_member_update_data,
)
from app.utils.member_filter import filter_keyword, filter_permission, filter_approve
from app.utils.member_sort import sort_accounts
from app.utils.pagination import paginate
from app.domains.account.validate.validate import validate_register
from app.domains.account.service.account_service import delete_account
from app import configs
from app.domains.account.permissions import PERMISSON

# ==========================================================
# 회원 관리 Blueprint 생성
# ==========================================================
# 회원 목록 조회, 회원 추가, 수정, 삭제 기능을 담당한다.
member_bp = Blueprint(
    "member",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/member/static",
)


# ==========================================================
# 회원 정보 수정
# ==========================================================
@member_bp.route("/member/update/<member_id>", methods=["POST"])
def member_update(member_id):

    # 계정 데이터 로드
    account_db = load_accounts()

    # 수정 폼 데이터 가져오기
    member_data = get_member_update_data(request)

    # 권한 및 승인 상태 수정
    success, message = update_member(
        account_db, member_id, member_data["permission"], member_data["approve"]
    )

    # 수정 실패
    if not success:
        return f"""
        <script>
        alert("{message}");
        history.back();
        </script>
        """

    # 변경사항 저장
    save_accounts(account_db)

    # 회원 목록 페이지 이동
    return redirect("/member/list")


# ==========================================================
# 회원 목록 조회
# ==========================================================
@member_bp.route("/member/list")
def member_list():

    # 로그인 여부 확인
    if "id" not in session:
        return redirect(url_for("main.main"))

    # 계정 데이터 로드
    account_db = load_accounts()

    # 딕셔너리를 리스트로 변환
    accounts = list(account_db.values())

    # 권한명을 화면에 표시하기 위한 데이터 추가
    for account in accounts:
        permissions = account[configs.KEY_PERMISSIONS]

        if PERMISSON.MEMBER_ACCESS.value in permissions:
            account["PERMISSION_NAME"] = "관리자"
        else:
            account["PERMISSION_NAME"] = "관제자"

    # 검색 및 정렬 옵션 가져오기
    options = get_member_list_options(request)

    # 검색
    accounts = filter_keyword(accounts, options["keyword"], options["tag"])

    accounts = filter_permission(accounts, options["permission"])

    accounts = filter_approve(accounts, options["approve"])

    # 정렬
    accounts = sort_accounts(accounts, options["sort"])

    # 페이지네이션
    accounts, total_pages = paginate(accounts, options["page"], options["per_page"])

    # 현재 로그인한 사용자 권한 표시
    if PERMISSON.MEMBER_ACCESS.value in session["permissions"]:
        user_permission = "관리자"
    else:
        user_permission = "관제자"

    # 회원 목록 화면 렌더링
    return render_template(
        "member_list.html",
        user_permission=user_permission,
        user_id=session["id"],
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
        mode=options["mode"],
    )


# ==========================================================
# 회원 추가
# ==========================================================
@member_bp.route("/member/add", methods=["POST"])
def member_add():

    # 계정 데이터 로드
    account_db = load_accounts()

    # 관리자 권한 확인
    # if not is_admin(session.get("id")):
    #     return """
    #     <script>
    #     alert("권한이 없습니다.");
    #     history.back();
    #     </script>
    #     """

    # 입력 데이터 가져오기
    member_data = get_member_add_data(request)

    # 회원가입 검증
    success, field, message, phone = validate_register(
        account_db,
        member_data["id"],
        member_data["pw"],
        member_data["email"],
        member_data["phone1"],
        member_data["phone2"],
        member_data["phone3"],
    )

    # 검증 실패
    if not success:
        return render_template(
            "create_account.html",
            error_field=field,
            error_message=message,
            member_data=member_data,
        )

    # 전화번호 저장
    member_data["phone"] = phone

    # 계정 생성
    account_db[member_data["id"]] = make_member(member_data)

    # 계정 저장
    save_accounts(account_db)

    # 회원 목록 이동
    return render_template(
        "main_index.html",
        message="회원가입 요청이 완료되었습니다. 승인을 기다려주세요.",
        success=True,
    )


# ==========================================================
# 회원 삭제
# ==========================================================
@member_bp.route("/member/delete/<member_id>")
def member_delete(member_id):

    # 계정 데이터 로드
    account_db = load_accounts()

    # 관리자 권한 확인
    if not is_admin(session["id"]):
        return """
        <script>
        alert("권한이 없습니다.");
        history.back();
        </script>
        """

    # 회원 삭제 및 삭제 ID 저장
    result, message = delete_account(account_db, member_id)

    # 삭제 성공
    if result:
        return redirect("/member/list")

    # 삭제 실패
    return f"""
    <script>
        alert("{message}");
        history.back();
    </script>
    """
