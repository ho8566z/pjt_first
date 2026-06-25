from flask import Blueprint

main_bp = Blueprint("main", __name__, template_folder="templates")


@main_bp.route("/")
def main():
    return "여긴 메인임"
