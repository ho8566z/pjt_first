import threading
import time
import numpy as np
from cv2 import VideoCapture
from cv2 import CAP_PROP_POS_FRAMES
from cv2 import CAP_PROP_FPS
from collections import deque

VIDEO = "video"
BLACK_SCREEN = np.zeros((1080, 1920, 3), np.uint8)

FRAME_DEFAULT = 24
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

    def __init__(self, src_path):
        self.src_path = src_path
        self.camera = None
        self.is_paused = False

        self.frame_queue = deque(maxlen=3)
        self.frame_queue.append(BLACK_SCREEN.copy())

        self.on_running = False
        self.thread = None
        self.lock = threading.Lock()

        self.connect()
        self.start()

# =================================================
# 기존 카메라 연결을 해제하고 지정된 소스 경로(src_path)로 
# 새로 영상을 연결합니다.
# =================================================
    def connect(self):
        if self.camera is not None:
            self.camera.release()

        self.camera = VideoCapture(self.src_path)

# =================================================
# 캡처 스레드가 멈춰 있다면 데몬 스레드로 캡처 루프를 새로 
# 실행합니다.
# =================================================
    def start(self):
        self.is_paused = False

        if not self.on_running:
            self.on_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

# =================================================
# 백그라운드에서 실시간 영상을 끊임없이 읽어와 프레임 
# 큐(deque)에 저장을 반복합니다. (실패 시 재연결)
# =================================================
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

# =================================================
# 스레드 충돌 없이 안전하게 가장 오래된 프레임을 꺼내어 
# 반환합니다. (부족 시 최신 프레임 유지)
# =================================================
    def read_frame(self):
        with self.lock:
            if len(self.frame_queue) > 1:
                return self.frame_queue.popleft()
            else:
                return self.frame_queue[0]

# =================================================
# 캡처 스레드를 정지시키고 카메라 리소스 연결을 완전히 해제합니다.
# =================================================
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

    def __init__(
        self,
        src_path,
    ):
        self.src_path = src_path
        self.camera = None
        self.is_paused = False

        self.frame_queue = deque(maxlen=3)
        self.frame_queue.append(BLACK_SCREEN.copy())

        self.on_running = False
        self.thread = None
        self.event = threading.Event()
        self.lock = threading.Lock()

        self.connect()
        self.start()

# =================================================
# 비디오 파일 스트림을 Open/재연결합니다.
# =================================================
    def connect(self):
        if self.camera is not None:
            self.camera.release()

        self.camera = VideoCapture(self.src_path)

# =================================================
# 일시정지 상태를 해제하고, 동영상 캡처 스레드를 시작하거나 
# 재개합니다.
# =================================================
    def start(self):
        self.is_paused = False

        if not self.on_running:
            self.on_running = True

            self.event.set()
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

        else:
            self.event.set()

# =================================================
# 백그라운드에서 동영상 프레임을 일정 FPS 간격으로 읽으며, 
# 영상이 끝나면 처음부터 무한 반복 재생시킵니다.
# =================================================
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

# =================================================
# 큐에서 프레임을 하나씩 꺼내 반환합니다.
# =================================================
    def read_frame(self):
        with self.lock:
            if len(self.frame_queue) > 1:
                return self.frame_queue.popleft()
            else:
                return self.frame_queue[0]

# =================================================
# 동영상 스레드를 완전히 종료하고 비디오 자원을 해제합니다.
# =================================================
    def release(self):
        self.on_running = False
        self.event.set()

        if self.thread is not None:
            self.thread.join()

        if self.camera and self.camera.isOpened():
            self.camera.release()

# =================================================
# 스레드를 종료하지 않고 동영상 재생을 일시정지시킵니다.
# =================================================
    def pause(self):
        self.event.clear()
        self.is_paused = True


# ================================================================
# 카메라 관리 함수들
# ================================================================

# =================================================
# 특정 ID로 실시간 카메라 또는 동영상을 생성하여 등록하고, 
# 해당 위치 좌표(위경도)를 할당합니다.
# =================================================
def add_camera(src_path, id, src_type=VIDEO):
    if id in _instances:
        print("이미 등록된 카메라입니다.")
        return False

    _instances[id] = (
        VideoCamera(src_path) if src_type == VIDEO else StreamCamera(src_path)
    )

    match src_path:
        case "tests/tokyo_street_trim01.mp4" | "tests/tokyo_street_trim02.mp4":
            _camera_coordinates[id] = (37.527420, 127.028330)
        case _:
            _camera_coordinates[id] = (36.3288, 127.4230)

    return True


# =================================================
# 등록된 카메라를 딕셔너리에서 제거하고 비동기 스레드로 자원을 안전하게 해제합니다.
# =================================================
def delete_camera(id):
    if id not in _instances:
        return

    cam = _instances[id]
    del _instances[id]

    # 안전 release
    threading.Thread(target=cam.release, daemon=True).start()


# =================================================
# 지정한 ID의 카메라/동영상 작동을 시작하거나 일시정지를 해제합니다.
# =================================================
def start_camera(id):
    if id not in _instances:
        return

    _instances[id].start()


# =================================================
# 실시간 카메라는 완전 해제(release), 동영상은 일시정지
# (pause)시킵니다.
# =================================================
def stop_camera(id):
    if id not in _instances:
        return

    cam = _instances[id]

    if isinstance(cam, StreamCamera):
        threading.Thread(target=cam.release, daemon=True).start()

    elif isinstance(cam, VideoCamera):
        cam.pause()


# =================================================
# 해당 ID의 카메라인지 일시정지 상태인지 여부를 반환합니다.
# =================================================
def is_paused_camera(id):
    if id not in _instances:
        return False

    return _instances[id].is_paused


# =================================================
# 해당 ID의 카메라이가 동영상 파일(VideoCamera) 인스턴스인지 
# 확인합니다.
# =================================================
def is_video_camera(id):
    if id not in _instances:
        return False

    return True if isinstance(_instances[id], VideoCamera) else False


# =================================================
# 등록된 모든 카메라를 한 번에 안전하게 삭제 및 정지시킵니다.
# =================================================
def clear():
    for id in tuple(_instances.keys()):
        delete_camera(id)


# =================================================
# 해당 ID 카메라의 최신 프레임을 꺼내 반환합니다. 
# (없을 시 검은 화면 반환)
# =================================================
def get_frame_by_id(id):
    "반환되는 frame은 레퍼런스 타입"
    if id not in _instances:
        return BLACK_SCREEN

    return _instances[id].read_frame()


# =================================================
# 현재 등록된 모든 카메라 ID 목록을 튜플 형태로 반환합니다.
# =================================================
def get_all_camera_ids():
    return tuple(_instances.keys())


# =================================================
# ID에 해당하는 카메라 객체 자체를 가져옵니다.
# =================================================
def get_camera_by_id(id):
    return _instances.get(id)


# =================================================
# 해당 카메라 ID의 위도/경도 위치 좌표를 반환합니다.
# =================================================
def get_camera_coordinate(id):
    return _camera_coordinates.get(id)
