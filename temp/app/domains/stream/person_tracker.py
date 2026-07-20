import time
from concurrent.futures import ThreadPoolExecutor

from ultralytics import YOLO
from ultralytics.utils import YAML
from ultralytics.utils.checks import check_yaml
from ultralytics.utils import IterableSimpleNamespace
from ultralytics.trackers.bot_sort import BOTSORT
from ultralytics.utils.plotting import Annotator, colors
from cv2 import imwrite

from app.domains.stream import face_profiler
from app.domains.stream.camera import get_camera_coordinate
from app.domains.logger.event_logs.event_logs import create_event_data

_model = YOLO("yolov8n.pt")
_trackers = {}  # camera_id: tracker
_tracker_caches = {}  # camera_id: { track_id: {...}, ...}

# predictor 강제 생성
_model.overrides["conf"] = 0.4
_model.overrides["iou"] = 0.55
_model.overrides["imgsz"] = 640
_model.overrides["verbose"] = False
_model.overrides["classes"] = [0]

IDENTIFY_RETRY_INTERVAL = 1
IDENTIFY_RECHECK_INTERVAL = 30
LOGGING_INTERVAL = 15

_executor = ThreadPoolExecutor(max_workers=8)


# =================================================
# 카메라별로 개별 BoT-SORT 객체 추적기를 생성하고 관리하여 
# multi-camera 객체 ID가 서로 엉키지 않도록 독립된 캐시 
# 공간을 할당합니다.
# =================================================
def get_or_create_tracker(camera_id):
    if camera_id not in _trackers:
        tracker_yaml = check_yaml("botsort.yaml")
        tracker_data = YAML.load(tracker_yaml)  # 딕셔너리로 변환됨
        tracker_data.update(_model.overrides)
        cfg = IterableSimpleNamespace(**tracker_data)

        _trackers[camera_id] = BOTSORT(args=cfg)
        _tracker_caches[camera_id] = {}

    return _trackers[camera_id]


# =================================================
# 얼굴 식별(AI 연산) 시 프레임이 멈추는 병목 현상을 막기 위해, 
# 최대 8개의 백그라운드 스레드에서 비동기로 얼굴을 비교하고 
# 결과를 캐시(_tracker_caches)에 업데이트합니다.
# =================================================
def track_all(frames: list, camera_ids):
    results = _model.predict(frames, stream=True)
    frames_output = [frame.copy() for frame in frames]

    for frame, result, camera_id in zip(frames_output, results, camera_ids):
        tracker = get_or_create_tracker(camera_id)

        # 탐지된 객체가 없는 경우
        if result.boxes is None or len(result.boxes) == 0:
            tracker.update(result.boxes, frame)
            frames_output.append(frame)
            continue

        # tracks: [[x1, y1, x2, y2, track_id, conf, cls_id], ...]
        tracks = tracker.update(result.boxes, frame)
        annotator = Annotator(frame, line_width=2)

        for track in tracks:
            x1, y1, x2, y2, track_id, conf, cls_id = track[:7]
            box = [int(x1), int(y1), int(x2), int(y2)]

            annotator.box_label(box, "", color=colors(int(track_id), True))

    return frames_output


# =================================================
# 입력된 프레임에서 사람(Class 0)을 탐지하고 바운딩 박스와 
# 추적 ID만 프레임에 그려서 반환하는 단순 추적 함수입니다.
# =================================================
def _async_identify(camera_id, track_id, person_img):
    try:
        user_id, match_ratio = face_profiler.identify(person_img)

        cache = _tracker_caches.get(camera_id)
        if cache is None or track_id not in cache:
            return

        cache[track_id]["user_id"] = user_id
        cache[track_id]["match_ratio"] = match_ratio

    finally:
        cache = _tracker_caches.get(camera_id)
        if cache is not None and track_id in cache:
            cache[track_id]["in_flight"] = False


# =================================================
'''
객체 추적: YOLOv8 + BoT-SORT로 화면 속 사람의 위치와 추적 
    ID(track_id)를 파악합니다.

비동기 식별 요청 제한:

미인식 인물은 1초 간격(IDENTIFY_RETRY_INTERVAL), 이미 인식된 
    인물은 30초 간격(IDENTIFY_RECHECK_INTERVAL)으로 재조회 
    주기를 조절하여 GPU/CPU 과부하를 방지합니다.

in_flight 플래그를 두어 동일 ID에 대해 중복 스레드 요청이 
    들어가지 않도록 제어합니다.

인식 객체 시각화 및 이벤트 로깅:

DB에 등록된 인물일 경우 화면에 이름 (유사도) 라벨을 시각화합니다.

15초 간격(LOGGING_INTERVAL)으로 이벤트 캡처 이미지를 
    저장(imwrite)하고 위치 정보와 함께 이벤트 데이터베이스 
    로그(create_event_data)를 생성합니다.

메모리 정리: 화면에서 사라진 추적 대상(dead track_id)의 
    캐시를 자동으로 삭제하여 메모리 누수를 방지합니다.
'''
# =================================================
def track_identified(frames: list, camera_ids) -> list:
    """프레임을 리스트로 받아서 각 프레임들을 분석 후 db에 등록된 사람에게만 주석을 달아서 반환"""
    results = _model.predict(frames, stream=True)
    frames_output = []

    for frame, result, camera_id in zip(frames, results, camera_ids):
        annotated_frame = frame.copy()

        tracker = get_or_create_tracker(camera_id)
        cache = _tracker_caches[camera_id]
        current_time = time.time()

        # 탐지된 객체가 없는 경우
        if result.boxes is None or len(result.boxes) == 0:
            tracker.update(result.boxes, annotated_frame)
            frames_output.append(annotated_frame)
            continue

        tracks = tracker.update(result.boxes, annotated_frame)
        annotator = Annotator(annotated_frame, line_width=2)

        height, width, _ = annotated_frame.shape
        clamper = (0, 0, width, height)

        active_track_ids = set()

        for track in tracks:
            x1, y1, x2, y2, track_id, _, _ = track[:7]

            box = [int(x1), int(y1), int(x2), int(y2)]
            track_id = int(track_id)
            active_track_ids.add(track_id)

            if track_id not in cache:
                cache[track_id] = {
                    "user_id": "",
                    "match_ratio": -1.0,
                    "last_requested": 0.0,
                    "last_logging": 0.0,
                    "in_flight": False,
                }

            user_cache = cache[track_id]

            # 이미 신원이 확정된 track은 재조회 주기 확대.
            retry_interval = (
                IDENTIFY_RETRY_INTERVAL
                if user_cache["user_id"] == ""
                else IDENTIFY_RECHECK_INTERVAL
            )

            should_request = (
                not user_cache["in_flight"]
                and current_time - user_cache["last_requested"] > retry_interval
            )

            if should_request:
                user_cache["last_requested"] = current_time

                clamped = clamp_boundary(box, clamper)
                crop = crop_frame(frame, clamped)

                if crop is not None and crop.size > 0:
                    user_cache["in_flight"] = True
                    _executor.submit(_async_identify, camera_id, track_id, crop)

            if user_cache["user_id"] != "":
                label = f"{user_cache['user_id']} ({user_cache['match_ratio']:.2f})"
                annotator.box_label(box, label, color=colors(track_id, True))

                if current_time - user_cache["last_logging"] > LOGGING_INTERVAL:
                    user_id = user_cache["user_id"]
                    coord = get_camera_coordinate(camera_id)
                    imwrite(
                        f"app/static/img/event_img/{user_id}_{track_id}.jpg",
                        annotated_frame,
                    )
                    create_event_data(
                        coord[0], coord[1], user_id, f"{user_id}_{track_id}.jpg"
                    )

                    user_cache["last_logging"] = current_time

        # dead track_id 캐시 정리 (메모리 누수 방지)
        for tid in tuple(cache.keys()):
            if tid not in active_track_ids:
                del cache[tid]

        frames_output.append(annotated_frame)

    return frames_output


# =================================================
# 객체의 바운딩 박스가 전체 영상의 경계선(너비, 높이)을 
# 벗어나지 않도록 좌표값을 안전하게 제한(Clamp)합니다.
# =================================================
def clamp_boundary(boundary_origin, clamper):
    x1, y1, x2, y2 = boundary_origin
    c_x1, c_y1, c_x2, c_y2 = clamper

    y1, y2 = max(c_y1, y1), min(c_y2, y2)
    x1, x2 = max(c_x1, x1), min(c_x2, x2)

    return (x1, y1, x2, y2)


# =================================================
# 전달받은 제한 좌표를 기반으로 영상 프레임에서 탐지된 사람 
# 영역만 크롭(Crop)하여 얼굴 식별 모듈로 전달합니다.
# =================================================
def crop_frame(frame, boundary):
    if frame is None:
        return None

    x1, y1, x2, y2 = boundary
    return frame[y1:y2, x1:x2]
