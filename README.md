# 🎯 카번개루스 (KABORNERUS) 화력운용 시스템

**Palantir Edge AI 기반 3D 전장 가시화 및 실시간 드론 화력 유도 시뮬레이터**

> ⚠️ 본 시스템은 교육·연구·데모 목적의 시뮬레이터입니다. 실제 무기체계와 무관합니다.

## 시스템 구조

```
┌─────────────────────────────────────────────────────┐
│  DroneVideoPanel(좌) │ CesiumMap3D(우)               │
│  UAV 영상 + AI 탐지  │ 3D 지형 + 피해 돔 렌더링      │
├──────────────────────────────────────────────────────┤
│  FireMissionLog (하단) — 화력 임무 이력              │
└──────────────────────────────────────────────────────┘
```

## 빠른 시작

```bash
# 백엔드
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 프론트엔드
cd frontend && npm install && npm run dev

# Docker 원클릭
docker-compose up --build
```

## 기술 스택
- **백엔드**: FastAPI + WebSocket + YOLOv8 ONNX + uvloop
- **프론트엔드**: React 18 + TypeScript (strict) + CesiumJS + Leaflet
- **AI**: YOLOv8n → ONNX FP32 → 실시간 군사 표적 탐지
- **통신**: MIL-STD-6016 J-series 기반 커스텀 바이너리 패킷
- **지도**: CesiumJS 3D 피해 돔 + Leaflet 2D 전술 지도

## 기능
- 실시간 드론/UAV 영상 스트리밍 (WebSocket)
- YOLOv8 AI 군사 표적 자동 탐지 (러시아 2S19, 북한 M1978 등)
- Carleton Damage Function 기반 3D 피해 반경 렌더링
- 타격수단 자동 권고 (Kill Chain)
- 화력 임무 승인 → J7 패킷 전송
- 재타격 부대 자동 선정
