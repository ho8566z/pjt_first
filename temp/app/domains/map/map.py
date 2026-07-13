from app.utils.json_manager import (
    load_json, 
    EVENT_LOGS_FILE, 
    TARGETS_PROFILES_FILE
)
from app import configs
import hashlib

# 타겟 id를 해시(md5)로 변환해서 항상 같은 색상이 나오도록 생성
# (같은 타겟이면 언제 호출해도 동일한 hsl 색상값 반환)
def get_color(target_id):
        
        value = int(hashlib.md5(target_id.encode()).hexdigest(), 16)
        hue = value % 360
        return f"hsl({hue}, 80%, 45%)"

# 지도 표시용 데이터를 만드는 함수
# target_id가 주어지면 해당 타겟만, 없으면 전체 타겟 데이터를 반환
def get_map_data(target_id=None):
    # event_logs.json / target_profiles.json 데이터 로드
    event_logs = load_json(EVENT_LOGS_FILE) or {}
    target_profiles = load_json(TARGETS_PROFILES_FILE) or {}
    
    # 타겟 id별로 로그를 묶어서 저장할 딕셔너리
    # { target_id : [log1, log2, ...] }
    target_logs = {}
    for log in event_logs.values():
        log_target_id = log.get(configs.KEY_TARGET_ID)

        # target_id가 없는(비정상) 로그는 건너뜀
        if not log_target_id:
             continue
        
        # target_id 인자가 넘어온 경우, 해당 타겟의 로그만 필터링
        if target_id is not None and log_target_id != target_id:
             continue

        # 처음 등장하는 target_id면 빈 리스트로 초기화
        if log_target_id not in target_logs:
            target_logs[log_target_id] = []
        
        # 해당 타겟의 로그 리스트에 현재 로그 추가
        target_logs[log_target_id].append(log)
   
    # 최종적으로 지도에 넘겨줄 데이터 리스트
    map_data = []
    
    # 타겟별로 로그를 가공해서 map_data에 담기
    for log_target_id, logs in target_logs.items():
        # 등록일시(REG_DATE) 기준 오름차순 정렬 (오래된 것 → 최신 순)
        logs.sort(key=lambda x: x[configs.KEY_REG_DATE])

        # 최근 로그 n개(10개)만 사용 (너무 많은 로그로 인한 부하 방지)
        logs = logs[-10:]

        # 가장 마지막(최신) 로그 = 타겟의 현재 위치로 사용(여기에 마커가 위치한다)
        latest_log = logs[-1]

        # 폴리라인(이동 경로) 표시용으로 로그를 균등 간격 샘플링
        # (로그 전체를 다 찍으면 너무 촘촘하니 5등분 정도로 추림)
        step = max(1, len(logs) // 5)
        sampled_logs = logs[::step]

        # 해당 타겟의 프로필 정보 조회
        target = target_profiles.get(log_target_id)

        # 프로필이 없는 타겟(고아 로그)은 건너뜀
        if not target:
             continue

        # 샘플링 과정에서 마지막(최신) 로그가 빠졌을 경우 강제로 포함
        # (현재 위치는 항상 경로에 포함되도록 보장)
        if sampled_logs[-1] != logs[-1]:
            sampled_logs.append(logs[-1])
    
        # 지도에 표시할 타겟 1건의 데이터 구성
        map_data.append({
            "id" : target[configs.KEY_ID],
            "name": target[configs.KEY_NAME],
            "age" : target[configs.KEY_AGE], 
            "short_description" : target[configs.KEY_SHORT_DESC], 
            "description" : target[configs.KEY_DESC], 
            "image" : target.get(configs.KEY_IMAGE), 
            
            #target 별 line색상
            "color": get_color(log_target_id),
            
            #현재위치
            "latitude" : latest_log[configs.KEY_EVENT_LAT], 
            "longitude" : latest_log[configs.KEY_EVENT_LON],
            
            #이동 경로 (샘플링된 로그 좌표들)
            "logs": sampled_logs,
            
            #등록 일시 (최신 로그 기준)
            "reg_date" : latest_log[configs.KEY_REG_DATE],
        })
    return map_data