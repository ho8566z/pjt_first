import os
from cv2 import imdecode, IMREAD_COLOR
from numpy import frombuffer, uint8
from werkzeug.utils import secure_filename

from app.utils.json_manager import load_json, save_json, TARGETS_PROFILES_FILE, BASE_DIR
from app.utils.time_stamper import get_current_time_stamp_formated
from app.utils.member_filter import filter_keyword
from app.utils.member_sort import sort_accounts
from app.utils.pagination import paginate
from app.domains.stream.face_profiler import add_or_update_face


def handle_add_profile(form_data, files, static_folder):
    profiles = load_json(TARGETS_PROFILES_FILE)
    pid = form_data.get("id")

    if pid in profiles:
        return False

    name = form_data.get("name")
    age = form_data.get("age")
    desc_short = form_data.get("description_short")
    desc_long = form_data.get("description_long")

    file = files.get("profile_img")
    upload_path = os.path.join(static_folder, "uploaded_profiles")
    os.makedirs(upload_path, exist_ok=True)
    file_name = secure_filename(f"{pid}")
    file.save(os.path.join(upload_path, file_name))

    time_formatted = get_current_time_stamp_formated()
    profiles[pid] = {
        "ID": pid,
        "NAME": name,
        "AGE": age,
        "SHORT_DESCRIPTION": desc_short,
        "DESCRIPTION": desc_long,
        "IMAGE": file_name,
        "REG_DATE": time_formatted,
        "MOD_DATE": time_formatted,
    }
    save_json(TARGETS_PROFILES_FILE, profiles)
    return True


def handle_update_profile(form_data, files, static_folder):
    profiles = load_json(TARGETS_PROFILES_FILE)
    pid = form_data.get("id")
    if pid in profiles:
        profiles[pid]["NAME"] = form_data.get("name")
        profiles[pid]["AGE"] = form_data.get("age")
        profiles[pid]["SHORT_DESCRIPTION"] = form_data.get("description_short")
        profiles[pid]["DESCRIPTION"] = form_data.get("description_long")
        profiles[pid]["MOD_DATE"] = get_current_time_stamp_formated()

        file = files.get("profile_img")
        if file and file.filename != "":
            upload_path = os.path.join(static_folder, "uploaded_profiles")
            os.makedirs(upload_path, exist_ok=True)
            file_name = secure_filename(f"{pid}")
            profiles[pid]["IMAGE"] = file_name
            file.save(os.path.join(upload_path, file_name))

        save_json(TARGETS_PROFILES_FILE, profiles)


def handle_face_encode(form_data, files):
    pid = form_data.get("id")
    face_file = files.get("face_img")
    if face_file and face_file.filename != "":
        file_bytes = face_file.read()
        img = imdecode(frombuffer(file_bytes, dtype=uint8), IMREAD_COLOR)
        add_or_update_face(pid, img)


def handle_delete_profile(form_data, static_folder):
    profiles = load_json(TARGETS_PROFILES_FILE)
    pid = form_data.get("id")
    if pid in profiles:
        del profiles[pid]
    save_json(TARGETS_PROFILES_FILE, profiles)

    file_path = os.path.join(BASE_DIR, "face_embeddings", pid)
    if os.path.exists(file_path):
        os.remove(file_path)

    os.remove(os.path.join(static_folder, "uploaded_profiles", pid))


def get_paginated_profiles(args):
    profiles_list = list(load_json(TARGETS_PROFILES_FILE).values())

    kwd = args.get("search_keyword")
    tag = args.get("search_tag")
    profiles_list = filter_keyword(profiles_list, kwd, tag)

    order = args.get("sort_order")
    profiles_list = sort_accounts(profiles_list, order)

    per_page = int(args.get("per_page", 10))
    page = int(args.get("page", 1))
    profiles_paginated, total_pages = paginate(profiles_list, page, per_page)

    return profiles_paginated, page, per_page, total_pages
