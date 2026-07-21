import os
from flask import Blueprint, render_template, request
from .map import get_map_data

# 현재 파일(routes.py)이 위치한 디렉토리 경로
# (템플릿/정적 파일 경로 설정 등에 활용될 수 있음)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 'map' 기능을 위한 블루프린트 생성
# 이 블루프린트 전용 templates/static 폴더를 지정
map_bp = Blueprint(
    "map",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/map/static",
)


# GET /map 요청 처리
# 쿼리스트링으로 target_id가 오면 해당 타겟만, 없으면 전체 타겟 지도 데이터를 렌더링
@map_bp.route("/map")
def map_page():
    # URL 쿼리 파라미터에서 target_id 추출 (예: /map?target_id=abc123)
    target_id = request.args.get("target_id")

    # target_id 유무에 따라 필터링된(또는 전체) 지도 데이터 조회
    maps = get_map_data(target_id)

    # map.html 템플릿에 지도 데이터를 넘겨 렌더링
    return render_template("map.html", maps=maps)


# 전체 타겟의 지도 데이터를 그대로 반환하는 헬퍼 함수
# (target_id 필터 없이 get_map_data()를 호출)
def load_maps():
    return get_map_data()