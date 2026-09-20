import threading
import time
import numpy as np
from cv2 import VideoCapture
from cv2 import CAP_PROP_POS_FRAMES
from cv2 import CAP_PROP_FPS
from collections import deque
from app.utils import json_manager

VIDEO = "video"
BLACK_SCREEN = np.zeros((1080, 1920, 3), np.uint8)

FRAME_DEFAULT = 15
CONNECT_DELAY = 0.5
UNSTABLE_STREAMING_DELAY = 0.1
CPU_USAGE_DELAY = 0.001

_instances = {}
_camera_coordinates = {}


class StreamCamera:
    """
    백그라운드(thread)에서 카메라의 최신 프레임을 확보 및 제공하는 클래스.
    최초 생성시 아무런 프레임도 확보하지 못하면 검은 화면 반환
    반환되는 frame은 레퍼런스
    """

    def __init__(self, src_path, is_decoy=False):
        self.src_path = src_path
        self.camera = None
        self.is_paused = False
        self.is_decoy = is_decoy

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
        self.is_paused = False

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
        self.is_paused = True

        if self.thread is not None:
            self.thread.join()

        if self.camera and self.camera.isOpened():
            self.camera.release()


class VideoCamera:
    """
    백그라운드(thread)에서 비디오 파일의 최신 프레임을 확보 및 제공하는 클래스.
    최초 생성시 아무런 프레임도 확보하지 못하면 검은 화면 반환
    반환되는 frame은 레퍼런스
    """

    def __init__(self, src_path, is_decoy=False):
        self.src_path = src_path
        self.camera = None
        self.is_paused = False
        self.is_decoy = is_decoy

        self.frame_queue = deque(maxlen=3)
        self.frame_queue.append(BLACK_SCREEN.copy())

        self.on_running = False
        self.thread = None
        self.event = threading.Event()
        self.lock = threading.Lock()

        self.connect()
        self.start()

    def connect(self):
        if self.camera is not None:
            self.camera.release()

        self.camera = VideoCapture(self.src_path)

    def start(self):
        self.is_paused = False

        if not self.on_running:
            self.on_running = True

            self.event.set()
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

        else:
            self.event.set()

    def _capture_loop(self):
        fps = self.camera.get(CAP_PROP_FPS)

        if fps <= 0:
            fps = FRAME_DEFAULT

        frame_delay = 1.0 / FRAME_DEFAULT

        while self.on_running:
            self.event.wait()

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

            # 동영상이 끝나면 처음부터 다시 재생.
            else:
                self.camera.set(CAP_PROP_POS_FRAMES, 0)

    def read_frame(self):
        with self.lock:
            if len(self.frame_queue) > 1:
                return self.frame_queue.popleft()
            else:
                return self.frame_queue[0]

    def release(self):
        self.on_running = False
        self.event.set()

        if self.thread is not None:
            self.thread.join()

        if self.camera and self.camera.isOpened():
            self.camera.release()

    def pause(self):
        self.event.clear()
        self.is_paused = True


# ================================================================
# 카메라 관리 함수들
# ================================================================
def add_camera(src_path, id, src_type=VIDEO):
    if id in _instances:
        print("이미 등록된 카메라입니다.")
        return False

    decoy = False

    match id:
        case "0" | "1":
            pass
        case _:
            decoy = True

    _instances[id] = (
        VideoCamera(src_path, is_decoy=decoy)
        if src_type == VIDEO
        else StreamCamera(src_path, is_decoy=decoy)
    )

    match src_path:
        case "tests/tokyo.mp4":
            _camera_coordinates[id] = (37.5235, 127.0430)
        case "tests/jungho.mp4":
            _camera_coordinates[id] = (37.5070, 127.0379)
        case _:
            _camera_coordinates[id] = (36.3288, 127.4230)

    save_cameras()
    return True


def delete_camera(id):
    if id not in _instances:
        return

    cam = _instances[id]
    del _instances[id]

    # 안전 release
    threading.Thread(target=cam.release, daemon=True).start()
    save_cameras()


def start_camera(id):
    if id not in _instances:
        return

    _instances[id].start()
    save_cameras()


def stop_camera(id):
    if id not in _instances:
        return

    cam = _instances[id]

    if isinstance(cam, StreamCamera):
        threading.Thread(target=cam.release, daemon=True).start()

    elif isinstance(cam, VideoCamera):
        cam.pause()

    save_cameras()


def is_paused_camera(id):
    if id not in _instances:
        return False

    return _instances[id].is_paused


def is_decoy_camera(id):
    if id not in _instances:
        return False

    return _instances[id].is_decoy


def is_video_camera(id):
    if id not in _instances:
        return False

    return True if isinstance(_instances[id], VideoCamera) else False


def clear():
    for id in tuple(_instances.keys()):
        delete_camera(id)

    save_cameras()


def get_frame_by_id(id):
    "반환되는 frame은 레퍼런스 타입"
    if id not in _instances:
        return BLACK_SCREEN

    return _instances[id].read_frame()


def get_all_camera_ids(on_activated=True):

    if on_activated:
        return tuple([id for id in _instances if not is_paused_camera(id)])

    return tuple(_instances.keys())


def get_camera_by_id(id):
    return _instances.get(id)


def get_camera_coordinate(id):
    return _camera_coordinates.get(id)


def init_cameras():
    load_cameras()


def load_cameras():
    loaded_cameras = json_manager.load_json(json_manager.CAMERAS_FILES)

    for camera_id in loaded_cameras:
        camera = loaded_cameras[camera_id]

        add_camera(camera["src_path"], camera_id, camera["src_type"])

        if camera["is_paused"]:
            stop_camera(camera_id)


def save_cameras():
    camera_json = {}

    for camera_id in get_all_camera_ids(on_activated=False):
        camera_json[camera_id] = {
            "id": camera_id,
            "src_path": get_camera_by_id(camera_id).src_path,
            "src_type": "video" if is_video_camera(camera_id) else "stream",
            "is_paused": is_paused_camera(camera_id),
        }

    json_manager.save_json(json_manager.CAMERAS_FILES, camera_json)
