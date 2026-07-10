import threading
import time
import numpy as np
from cv2 import VideoCapture
from cv2 import CAP_PROP_POS_FRAMES
from collections import deque

VIDEO = "video"
BLACK_SCREEN = np.zeros((1080, 1920, 3), np.uint8)

FRAME_DEFAULT = 30
CONNECT_DELAY = 0.5
UNSTABLE_STREAMING_DELAY = 0.1
CPU_USAGE_DELAY = 0.001

_instances = {}
_camera_coordinates = {}


class Camera:
    """
    백그라운드(thread)에서 카메라의 최신 프레임을 확보 및 제공하는 클래스.
    최초 생성시 아무런 프레임도 확보하지 못하면 검은 화면 반환
    반환되는 frame은 레퍼런스
    """

    def __init__(self, src_path, src_type):
        self.src_path = src_path
        self.is_video = src_type == VIDEO
        self.camera = None

        self.frame_queue = deque(maxlen=3)
        self.frame_queue.append(BLACK_SCREEN.copy())

        self.on_running = False
        self.thread = None
        self.lock = threading.Lock()

        self.connect()
        self.start()

    def connect(self):
        if self.camera is not None:
            self.camera.release()

        self.camera = VideoCapture(self.src_path)

    def start(self):
        if not self.on_running:
            self.on_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

    def _capture_loop(self):
        frame_delay = 1.0 / FRAME_DEFAULT

        while self.on_running:
            if self.camera is None or not self.camera.isOpened():
                self.connect()
                time.sleep(CONNECT_DELAY)
                continue

            start_time = time.time()
            success, frame = self.camera.read()

            if success and frame is not None:
                with self.lock:
                    self.frame_queue.append(frame)

                processing_time = time.time() - start_time
                sleep_time = frame_delay - processing_time

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    time.sleep(CPU_USAGE_DELAY)

            # 동영상이 끝났거나, 스트리밍에서 프레임을 가져오지 못한 경우
            else:
                if self.is_video:
                    self.camera.set(CAP_PROP_POS_FRAMES, 0)
                else:
                    time.sleep(UNSTABLE_STREAMING_DELAY)

    def read_frame(self):
        with self.lock:
            if len(self.frame_queue) > 1:
                return self.frame_queue.popleft()
            else:
                return self.frame_queue[0]

    def release(self):
        self.on_running = False

        if self.thread is not None:
            self.thread.join()

        if self.camera and self.camera.isOpened():
            self.camera.release()


# ================================================================
# 카메라 관리 함수들
# ================================================================
def add_camera(src_path, id, src_type=VIDEO):
    if id in _instances:
        print("이미 등록된 카메라입니다.")
        return

    _instances[id] = Camera(src_path, src_type)

    match src_path:
        case "tests/tokyo_street_trim01.mp4" | "tests/tokyo_street_trim02.mp4":
            _camera_coordinates[id] = (37.527420, 127.028330)
        case _:
            _camera_coordinates[id] = (0.0, 0.0)


def delete_camera(id):
    if id not in _instances:
        return

    cam = _instances[id]
    del _instances[id]

    # 안전 release
    threading.Thread(target=cam.release, daemon=True).start()


def clear():
    for id in tuple(_instances.keys()):
        delete_camera(id)


def get_frame_by_id(id):
    "반환되는 frame은 레퍼런스 타입"
    if id not in _instances:
        return BLACK_SCREEN

    return _instances[id].read_frame()


def get_all_camera_ids():
    return tuple(_instances.keys())


def get_camera_by_id(id):
    return _instances.get(id)


def get_camera_coordinate(id):
    return _camera_coordinates.get(id)
