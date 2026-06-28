import os
from flask import Blueprint, render_template

current_dir = os.path.dirname(os.path.abspath(__file__))

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/main/static",
)


@main_bp.route("/")
def main():
    return render_template("main_index.html")
