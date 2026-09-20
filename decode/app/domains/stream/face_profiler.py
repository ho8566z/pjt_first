import threading
import os
import warnings

import numpy as np

from app.utils.mute_print_and_warnings import mute_print_and_warnings
from app.utils.json_manager import BASE_DIR

# library 워닝 지우기(deprecated)
warnings.filterwarnings("ignore", category=FutureWarning, module="insightface")
from insightface.app import FaceAnalysis  # noqa: E402

# ================================================================
# InsightFace: Lazy allocation
# ================================================================

FACE_DETECTION_SIZE = (128, 128)
_instance = None
_lock = threading.Lock()


@mute_print_and_warnings
def _create_face_app():
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        allowed_modules=["detection", "recognition"],
    )
    app.prepare(ctx_id=0, det_size=FACE_DETECTION_SIZE)

    return app


def get_face_app():
    global _instance

    # 병목 방지
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = _create_face_app()

    return _instance


# ================================================================
# Face 임베딩 저장/로딩/캐싱
# ================================================================

EMBEDDINGS_DIR = os.path.join(BASE_DIR, "face_embeddings")

_embedding_matrix_cache: np.ndarray = np.empty((0, 512))
_face_ids_cache: np.ndarray = np.array([])


def extract_embedding(face_img) -> np.ndarray | None:
    if face_img is None:
        return None

    faces = get_face_app().get(face_img)

    return None if not faces else faces[0].normed_embedding


def add_or_update_face(face_id: str, img) -> bool:
    new_embedding = extract_embedding(img)

    if new_embedding is None:
        print(f"[{face_id}] 얼굴 인식 실패: {img}")
        return False

    user_file_path = os.path.join(EMBEDDINGS_DIR, f"{face_id}.npz")

    new_vector_sum = None
    new_count = 0

    if os.path.exists(user_file_path):
        with np.load(user_file_path) as data:
            current_vector_sum = data["vector_sum"]
            current_count = data["count"]

        new_vector_sum = current_vector_sum + new_embedding
        new_count = current_count + 1

    else:
        new_vector_sum = new_embedding
        new_count = 1

    mean_vector = new_vector_sum / new_count
    new_norm_embedding = mean_vector / np.linalg.norm(mean_vector)

    np.savez_compressed(
        user_file_path,
        norm_embedding=new_norm_embedding,
        vector_sum=new_vector_sum,
        count=new_count,
    )

    init_load_all_embeddings()
    print(f"[{face_id}] 임베딩 업데이트 완료 (총 {new_count}장)")
    return True


def init_load_all_embeddings():
    global _embedding_matrix_cache, _face_ids_cache

    embeddings = []
    ids = []

    if not os.path.exists(EMBEDDINGS_DIR):
        return

    print("--- 메모리에 얼굴 임베딩 로드 시작 ---")
    for filename in os.listdir(EMBEDDINGS_DIR):
        if filename.endswith(".npz"):
            face_id = filename.replace(".npz", "")
            file_path = os.path.join(EMBEDDINGS_DIR, filename)

            with np.load(file_path) as data:
                embeddings.append(data["norm_embedding"])
                ids.append(face_id)

    if embeddings:
        _embedding_matrix_cache = np.array(embeddings)
        _face_ids_cache = np.array(ids)

    print(f"--- 총 {len(_embedding_matrix_cache)}명의 임베딩(평균값) 로드 완료 ---")


# ================================================================
# Face 임베딩 비교
# ================================================================

IDENTIFY_THREASHOLD = 0.45
NO_MATCH = ("", -1.0)


def identify(person_img) -> tuple[str, float]:
    """
    입력받은 사람 이미지와 db에 등록된 검색 대상들과의 얼굴 특징점 비교\n
    유사도가 임계값 이상인 경우 반환: (target_id:str, match_ratio:float)\n
    유사도가 임계값 이하인 경우 반환: ("", -1.0)
    """
    faces = get_face_app().get(person_img)

    if not faces:
        return NO_MATCH

    current_embedding = faces[0].normed_embedding

    similarities = np.dot(_embedding_matrix_cache, current_embedding)
    if len(similarities) == 0:
        return NO_MATCH

    best_idx = np.argmax(similarities)
    best_match_ratio = float(similarities[best_idx])

    if IDENTIFY_THREASHOLD > best_match_ratio:
        return NO_MATCH

    return (_face_ids_cache[best_idx], best_match_ratio)


if __name__ == "__main__":
    print(get_face_app().models["recognition"].session.get_providers())
