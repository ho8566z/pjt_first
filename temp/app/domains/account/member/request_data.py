def get_member_list_options(request):

    return {
        "keyword": request.args.get("keyword", "").strip(),
        "tag": request.args.get("tag", "전체"),
        "permission": request.args.get("permission", "전체"),
        "approve": request.args.get("approve", "전체"),
        "sort": request.args.get("sort", "최신등록순"),
        "per_page": int(request.args.get("per_page", 10)),
        "page": int(request.args.get("page", 1)),
        "edit_id": request.args.get("edit_id", ""),
        "mode": request.args.get("mode", "list"),
    }

def get_member_add_data(request):

    return {
        "id": request.form.get("id", "").strip(),
        "pw": request.form.get("pw", "").strip(),
        "name": request.form.get("name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "permission": request.form.get("permission", "관제자"),
        "approve": request.form.get("approve", "미승인"),
    }

def get_member_update_data(request):

    return {
        "permission": request.form.get("permission"),
        "approve": request.form.get("approve"),
    }