### dependency install ------

pip install -r requirements.txt -y

#### essentials

python version 3.12.0

1. opencv-python
2. ultralytics
3. flask

### Entry point ------

python app.py

#### project hierachy example

my_flask_app/
│
├── app/
│ ├── **init**.py # Flask 앱 팩토리 (Blueprint 등록)
│ ├── config.py # 환경 설정
│ │
│ ├── auth/ # 인증 서비스 도메인
│ │ ├── routes.py # Blueprint 정의 및 라우팅
│ │ ├── models.py # 회원 관련 DB 모델
│ │ ├── templates/ # auth 전용 템플릿
│ │ │ └── auth/
│ │ │ ├── login.html
│ │ │ └── register.html
│ │ └── static/ # auth 전용 CSS/JS
│ │ └── css/
│ │ └── auth.css
│ │
│ ├── main/ # 메인 페이지 및 공통 도메인
│ │ ├── routes.py
│ │ └── templates/
│ │ └── main/
│ │
│ └── templates/ # 앱 전체가 공유하는 공통 템플릿 (레이아웃 등)
│
├── run.py # 애플리케이션 실행 엔트리포인트
└── requirements.txt

### 기능구현 ------

#### 관제

1. 얼굴인식 O
2. 신원확인 O
3. 비인가 접근 로깅
   ? 데인저 존 설정
4. 임시로 접근 인가 (화면에서 대상 우클릭) 유효기간 설정, 연장
5. 감지 대상에서 배제 (화면에서 대상 우클릭)

#### 로그 처리

1. 관리자 활동 전체 로깅 (악용방지)
2. 사진, 시간, 대상 표시, 위치,
   ? 주변에 있는 대처 가능 인원들 파악
3. 처리 완료된 task 정리, 아카이브
4. 팝업, 현황 안내
   ? 디스코드나 카톡

#### 신원 등록 방법

1. 카메라로 동영상?
2. 미리 준비한 사진으로?

#### 악용 방지

### 문제점 ------

1. 사진, 딥페이크 등을 이용한 비인가 접근
   : 해결법-> liveness 체크 ? 패시브, 액티브
