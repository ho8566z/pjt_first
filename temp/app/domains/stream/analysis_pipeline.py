from app.domains.stream import camera
from app.domains.stream import person_tracker
import threading
import time


class FrameAnalyzer:
    def __init__(self):
        self.on_running = False
        self.thread = None
        self.lock = threading.Lock()

        self.latest_frames = {}
        self.start()

    def start(self):
        if not self.on_running:
            self.on_running = True
            self.thread = threading.Thread(target=self._analyze_loop, daemon=True)
            self.thread.start()

    def _analyze_loop(self):
        while self.on_running:
            camera_ids = camera.get_all_camera_ids()

            if not camera_ids:
                # 등록된 카메라가 없으면 대기
                time.sleep(0.1)
                continue

            frames = [camera.get_frame_by_id(id) for id in camera_ids]
            tracked_frames = person_tracker.track_identified(frames, camera_ids)
            # tracked_frames = person_tracker.track_all(frames, camera_ids)

            temp = {}
            for id, frame in zip(camera_ids, tracked_frames):
                temp[id] = frame

            with self.lock:
                self.latest_frames = temp

            time.sleep(0.001)

    def get_frame(self):
        with self.lock:
            return self.latest_frames

    def release(self):
        self.on_running = False

        if self.thread is not None:
            self.thread.join()


_instance = FrameAnalyzer()


def get_latest_frames():
    return _instance.get_frame()


if __name__ == "__main__":
    import cv2
    from app.domains.stream import face_profiler

    face_profiler.init_load_all_embeddings()

    URL1 = "tests/tokyo_street_trim01.mp4"
    # URL2 = "tests/tokyo_street_trim02.mp4"

    camera.add_camera(URL1, 0)
    # camera.add_camera(URL2, 1)

    while True:
        frames_dict = get_latest_frames()

        if not frames_dict:
            continue

        for cam_id, frame in frames_dict.items():
            if frame is None:
                continue

            cv2.imshow(f"{cam_id}", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
