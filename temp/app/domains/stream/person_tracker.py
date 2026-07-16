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


def get_or_create_tracker(camera_id):
    if camera_id not in _trackers:
        tracker_yaml = check_yaml("botsort.yaml")
        tracker_data = YAML.load(tracker_yaml)  # 딕셔너리로 변환됨
        tracker_data.update(_model.overrides)
        cfg = IterableSimpleNamespace(**tracker_data)

        _trackers[camera_id] = BOTSORT(args=cfg)
        _tracker_caches[camera_id] = {}

    return _trackers[camera_id]


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


def clamp_boundary(boundary_origin, clamper):
    x1, y1, x2, y2 = boundary_origin
    c_x1, c_y1, c_x2, c_y2 = clamper

    y1, y2 = max(c_y1, y1), min(c_y2, y2)
    x1, x2 = max(c_x1, x1), min(c_x2, x2)

    return (x1, y1, x2, y2)


def crop_frame(frame, boundary):
    if frame is None:
        return None

    x1, y1, x2, y2 = boundary
    return frame[y1:y2, x1:x2]
