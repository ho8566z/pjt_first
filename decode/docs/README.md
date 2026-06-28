### dependency install ------

pip install -r docs/requirements.txt

#### essentials

python version 3.12.0

1. opencv-python
2. ultralytics
3. flask

### Entry point ------

python main.py

#### project hierachy example

obsidian-shield/
│
├─app/
│ │
│ ├─domains/ # 도메인별로 서비스를 모아놓은 폴더
│ │ └main/
│ │
│ ├──static/ # 앱 전체가 공유하는 공통 static
│ └──templates/ # 앱 전체가 공유하는 공통 templates
│
├──run.py # 애플리케이션 실행 엔트리포인트
└──requirements.txt
