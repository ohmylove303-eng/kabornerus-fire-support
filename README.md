# ⚡ 우루루쾅 화력운용 시스템 (Ururukwang Fire Support System)

> **Palantir Edge AI 기반 3D 전장 가시화 및 실시간 드론 화력 유도 시뮬레이터**  
> YOLOv8 표적 탐지 · WebSocket 50ms 이하 실시간 스트림 · CesiumJS 3D 피해 돔 · MIL-STD-6016 J-series 패킷

![Version](https://img.shields.io/badge/version-1.0.0--DEMO-red)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-61dafb)
![License](https://img.shields.io/badge/license-DEMO--ONLY-yellow)

---

## 📋 목차

- [시스템 개요](#-시스템-개요)
- [아키텍처](#-아키텍처)
- [요구사항](#-요구사항)
- [빠른 시작 (Docker)](#-빠른-시작-docker)
- [수동 설치](#-수동-설치)
- [데모 실행](#-데모-실행)
- [YOLOv8 파인튜닝](#-yolov8-파인튜닝)
- [프로젝트 구조](#-프로젝트-구조)
- [API 문서](#-api-문서)
- [주의사항](#-주의사항)

---

## 🎯 시스템 개요

우루루쾅은 드론 영상에서 군사 표적을 실시간 탐지하고, 3D 지도 위에 피해 반경을 시각화하며, 화력 임무를 관리하는 **교육/시뮬레이션 목적** 시스템입니다.

### 핵심 기능

| 기능 | 상세 | 기술 |
|------|------|------|
| 🎥 실시간 드론 피드 | 최대 8대 동시 처리, 15fps | WebSocket + msgpack 바이너리 |
| 🔍 표적 자동 탐지 | 9개 군사 클래스, mAP≥0.75 목표 | YOLOv8m ONNX, <35ms 추론 |
| 🌐 3D 피해 돔 | 치사/위험/사상 반경 충격파 애니메이션 | CesiumJS Ellipsoid |
| 📡 저지연 전송 | 평균 46ms, 목표 <50ms | msgpack + TCP_NODELAY |
| 🗺️ 2D/3D/SPLIT 지도 | 탭 전환 전술 지도 | CesiumJS + Leaflet |
| 🔴 OCO 화력 주문표 | 2-click 안전 교전 승인 | J7 패킷 전송 |
| 🔄 재타격 부대 선정 | 자동 대안 부대 제안 | REST API |
| 🔒 JWT + RBAC 보안 | 역할별 접근 제어 | FastAPI + python-jose |

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (React + TS)                  │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │DroneVideoPanel│  │ CesiumMap3D │  │ WeaponOCOTable│  │
│  │  + BBox 오버 │  │ 피해돔 렌더 │  │ FireMissionLog│  │
│  └──────┬───────┘  └──────┬──────┘  └───────┬───────┘  │
│         │ WS Binary        │ REST            │ REST      │
└─────────┼──────────────────┼─────────────────┼──────────┘
          │                  │                 │
┌─────────┼──────────────────┼─────────────────┼──────────┐
│         │          BACKEND (FastAPI)          │          │
│  ┌──────▼───────┐  ┌──────▼──────┐  ┌───────▼───────┐  │
│  │ WS Streamer  │  │ Weapon API  │  │ FireMission API│  │
│  │ <50ms 목표   │  │ Dome 계산   │  │ J7 패킷 생성  │  │
│  └──────┬───────┘  └─────────────┘  └───────────────┘  │
│         │                                                │
│  ┌──────▼────────────────────────────────────────────┐  │
│  │         AI Pipeline (YOLOv8m ONNX)                │  │
│  │  Preprocess → Inference → NMS → 표적DB 매칭       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
          │ GPU/CPU
┌─────────▼──────────────────────────────────────────────┐
│              Edge Resource Manager                      │
│  우선도별 FPS 할당 · CPU 적응형 품질 조절 · 최대 8 드론  │
└────────────────────────────────────────────────────────┘
```

---

## 💻 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| OS | Ubuntu 20.04 / macOS 12 | Ubuntu 22.04 |
| CPU | 8코어 | 16코어 |
| RAM | 16GB | 32GB |
| GPU | — (CPU 모드) | RTX 3080 10GB+ |
| 저장공간 | 20GB | 50GB |
| Python | 3.11 | 3.11 |
| Node.js | 18+ | 20+ |
| Docker | 24+ | 24+ |

---

## 🚀 빠른 시작 (Docker)

### 1단계 — 클론

```bash
git clone https://github.com/ohmylove303-eng/ururukwang-fire-support.git
cd ururukwang-fire-support
```

### 2단계 — 환경변수 설정

```bash
cp .env.example .env
# .env 편집: CESIUM_ION_TOKEN, JWT_SECRET_KEY 입력
nano .env
```

### 3단계 — Docker Compose 실행

```bash
# GPU 있는 경우
docker-compose --profile gpu up --build

# CPU만 있는 경우
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

### 4단계 — 브라우저 접속

| 서비스 | URL |
|--------|-----|
| 🖥️ 프론트엔드 | http://localhost:3000 |
| ⚙️ 백엔드 API | http://localhost:8000 |
| 📚 API 문서 | http://localhost:8000/docs |

> **기본 로그인**: `admin` / `ururukwang2026!`

---

## 🔧 수동 설치

### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

export JWT_SECRET_KEY="your-secret-key-min-32-chars"
export DEMO_MODE=true

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드

```bash
cd frontend
npm install

echo "REACT_APP_CESIUM_ION_TOKEN=your_token_here" > .env.local
echo "REACT_APP_API_URL=http://localhost:8000" >> .env.local

npm run dev
# → http://localhost:3000
```

---

## 🎮 데모 실행

### 시나리오 1: 단일 드론 표적 탐지

```bash
cd backend
python scripts/demo_drone_simulator.py --drone-id URQ-01 --fps 15

# 브라우저에서:
# 1. http://localhost:3000 접속
# 2. 좌측 DroneVideoPanel에서 URQ-01 피드 확인
# 3. 표적 탐지 시 TargetSignalCard 자동 팝업
# 4. 3D 지도에 피해 돔 자동 렌더링
```

### 시나리오 2: 다중 드론 + 화력 임무

```bash
python scripts/demo_drone_simulator.py --drone-id URQ-01 &
python scripts/demo_drone_simulator.py --drone-id URQ-02 &

# 브라우저에서:
# 1. 우측 OCO 화력 주문표에서 표적 확인
# 2. 🎯 버튼 → ⚠확인 버튼 (2-click 안전 승인)
# 3. 교전 승인 → 3D 지도 돔 색상 변경 (녹색)
# 4. 🔄 재타격 버튼으로 대안 부대 확인
```

### 시나리오 3: 3D/2D/SPLIT 뷰 전환

```
상단 헤더 → [🌐 3D] [🗺️ 2D] [⊞ SPLIT] 버튼 클릭
```

---

## 🤖 YOLOv8 파인튜닝

```bash
cd ai

# 1. Roboflow 데이터셋 다운로드
python dataset/collect_datasets.py YOUR_ROBOFLOW_API_KEY

# 2. OSINT 커스텀 이미지 배치
# ai/dataset/custom/2S19_MSTA/    ← 최소 50장
# ai/dataset/custom/M1978_Koksan/ ← 최소 30장

# 3. 레이블링
pip install labelimg
labelimg ai/dataset/custom/2S19_MSTA

# 4. 데이터셋 통합
python dataset/merge_datasets.py

# 5. 파인튜닝 (100 epoch)
python train/finetune_ururukwang.py
# → ai/models/ururukwang_v1.pt
# → ai/models/ururukwang_v1.onnx
# → ai/models/ururukwang_v1_int8.tflite
```

### 지원 클래스

| ID | 클래스 | 설명 |
|----|--------|------|
| 0 | tank_generic | 전차 일반 |
| 1 | **2S19_MSTA** | 러시아 152mm 자주포 ★ |
| 2 | 2S3_Akatsiya | 러시아 152mm 자주포 구형 |
| 3 | **M1978_Koksan** | 북한 170mm 자주포 ★ |
| 4 | BM21_Grad | 러시아 122mm 다연장 |
| 5 | T72_series | T-72 계열 전차 |
| 6 | APC_IFV | 장갑차/보병전투차 |
| 7 | artillery_towed | 견인 야포 |
| 8 | truck_military | 군용 트럭 |

---

## 📁 프로젝트 구조

```
ururukwang-fire-support/
├── 📄 README.md
├── 📄 docker-compose.yml
├── 📄 .env.example
│
├── 🐍 backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── ai/
│   │   ├── target_pipeline.py
│   │   ├── export_pipeline.py
│   │   └── models/
│   ├── ws/
│   │   └── ultra_low_latency.py
│   ├── edge/
│   │   └── resource_manager.py
│   ├── comms/
│   │   └── military_packet.py
│   ├── security/
│   │   └── auth.py
│   └── scripts/
│       └── demo_drone_simulator.py
│
├── ⚛️  frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── DroneVideoPanel.tsx
│   │   │   ├── CesiumMap3D.tsx
│   │   │   ├── LeafletMap2D.tsx
│   │   │   ├── FireMissionLog.tsx
│   │   │   └── WeaponOCOTable.tsx
│   │   ├── engine/
│   │   │   ├── DamageDomeManager.ts
│   │   │   └── MultiDroneTracker.ts
│   │   ├── utils/
│   │   │   └── packetParser.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
└── 🤖 ai/
    ├── dataset/
    │   ├── collect_datasets.py
    │   ├── merge_datasets.py
    │   └── augment.py
    └── train/
        └── finetune_ururukwang.py
```

---

## 📡 API 문서

### WebSocket 엔드포인트

| 경로 | 설명 | 프로토콜 |
|------|------|----------|
| `ws://host:8000/ws/drone-feed/{drone_id}` | 드론 영상 + 탐지 결과 | Binary (msgpack) |
| `ws://host:8000/ws/drone-positions` | 드론 GPS 위치 스트림 | JSON |

### REST API

| Method | 경로 | 설명 |
|--------|------|------|
| POST | `/api/weapon-recommendation` | 표적 분석 + 타격수단 권고 |
| POST | `/api/fire-mission/approve` | 교전 승인 (JWT 필요) |
| POST | `/api/reattack` | 재타격 부대 선정 |
| GET | `/api/system/status` | 시스템 상태 |
| POST | `/auth/login` | JWT 토큰 발급 |

### 바이너리 패킷 구조

```
[2B magic=UR][4B seq][8B ts_ms][2B det_len][4B jpeg_len]
[det_len bytes: msgpack 탐지 데이터]
[jpeg_len bytes: JPEG 프레임]
```

---

## ⚠️ 주의사항

> **이 시스템은 교육 및 시뮬레이션 목적으로만 제작되었습니다.**

- 실제 군사 작전에 사용 불가
- 표적 데이터는 공개 OSINT 기반 시뮬레이션
- 군사 표준(MIL-STD-6016) 참조는 공개 문서 기반
- 개인정보 및 실제 군 작전 데이터 포함 금지

---

## 📜 라이선스

```
DEMO / EDUCATIONAL USE ONLY
이 소프트웨어는 교육, 연구, 시뮬레이션 목적으로만 사용 가능합니다.
실제 군사 작전에의 적용은 엄격히 금지됩니다.
```

---

<div align="center">
⚡ <b>우루루쾅 화력운용 시스템 v1.0 DEMO</b> ⚡
</div>
