# 카번개루스 백엔드 메인 — FastAPI + WebSocket + YOLOv8
import os
import time
import asyncio
import json
import struct
import hashlib
import hmac
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

import cv2
import numpy as np
import msgpack
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
import psutil

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECRET_KEY      = os.getenv("SECRET_KEY", "KABORNERUS_DEMO")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
DEMO_VIDEO      = os.getenv("DEMO_VIDEO_PATH", "demo/drone_feed_demo.mp4")
KST             = ZoneInfo("Asia/Seoul")

app = FastAPI(title="카번개루스 화력운용 API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 표적 데이터베이스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET_DB = {
    "2S19_MSTA_S":    {"type":"SPG","cal":"152mm","range_km":29,"priority":"HIGH",   "r0_m":55,"nation":"RU"},
    "2S3_Akatsiya":   {"type":"SPG","cal":"152mm","range_km":18,"priority":"HIGH",   "r0_m":55,"nation":"RU"},
    "2S7_Pion":       {"type":"SPG","cal":"203mm","range_km":47,"priority":"CRITICAL","r0_m":80,"nation":"RU"},
    "M1978_Koksan":   {"type":"SPG","cal":"170mm","range_km":40,"priority":"CRITICAL","r0_m":75,"nation":"NK"},
    "M1989_Juche_Po": {"type":"SPG","cal":"152mm","range_km":30,"priority":"HIGH",   "r0_m":55,"nation":"NK"},
    "BM21_Grad":      {"type":"MLRS","cal":"122mm","range_km":20,"priority":"HIGH",   "r0_m":40,"nation":"RU"},
    "T72_series":     {"type":"MBT", "cal":"125mm","range_km":0, "priority":"MEDIUM", "r0_m":25,"nation":"RU"},
    "truck_military": {"type":"LOG", "cal":"N/A",  "range_km":0, "priority":"LOW",    "r0_m":15,"nation":"??"},
}

WEAPON_MATRIX = {
    "CRITICAL": [
        {"weapon":"K9_Thunder_155mm","eta_min":3,"unit":"포병대대","weapon_id":1,"unit_id":10},
        {"weapon":"ATACMS_MGM140",   "eta_min":8,"unit":"군단미사일","weapon_id":5,"unit_id":50},
    ],
    "HIGH": [
        {"weapon":"K9_Thunder_155mm","eta_min":3,"unit":"포병대대","weapon_id":1,"unit_id":10},
        {"weapon":"AH64_Apache",     "eta_min":12,"unit":"항공대대","weapon_id":3,"unit_id":30},
    ],
    "MEDIUM": [
        {"weapon":"K105_Howitzer",   "eta_min":5,"unit":"포병중대","weapon_id":2,"unit_id":20},
        {"weapon":"Javelin_ATGM",    "eta_min":2,"unit":"대전차소대","weapon_id":4,"unit_id":40},
    ],
    "LOW":    [{"weapon":"관측 계속","eta_min":0,"unit":"감시소","weapon_id":0,"unit_id":0}],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# YOLOv8 모델 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    model = YOLO("yolov8n.pt")  # 초기: COCO, 이후 커스텀 파인튜닝 가중치로 교체
    print("[카번개루스] YOLOv8n 로드 완료")
except Exception as e:
    print(f"[카번개루스] 모델 로드 실패: {e}")
    model = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 유틸리티
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

import math
def calc_damage_radii(r0_m: float) -> dict:
    """Carleton Damage Function: P_kill(r)=exp(-(r/r0)^2)"""
    return {
        "lethal_m":   round(r0_m * math.sqrt(math.log(2)),   1),
        "danger_m":   round(r0_m * math.sqrt(math.log(10)),  1),
        "casualty_m": round(r0_m * math.sqrt(math.log(100)), 1),
    }

def parse_detections(results, frame_shape) -> list:
    detections = []
    if results is None:
        return detections
    for r in results:
        for box in r.boxes:
            cls_id   = int(box.cls)
            cls_name = model.names[cls_id]
            conf     = float(box.conf)
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            tgt = TARGET_DB.get(cls_name, {
                "type":"UNKNOWN","cal":"N/A","range_km":0,
                "priority":"LOW","r0_m":20,"nation":"??"
            })
            ts = int(time.time() * 1000)
            tgt_num = f"TGT-{datetime.now(KST).strftime('%H%M%S')}-{cls_id:02d}"
            detections.append({
                "class":      cls_name,
                "confidence": round(conf, 3),
                "bbox":       [x1,y1,x2,y2],
                "center_px":  [(x1+x2)//2,(y1+y2)//2],
                "target_info":    tgt,
                "damage_radii":   calc_damage_radii(tgt["r0_m"]),
                "weapon_recommendation": WEAPON_MATRIX.get(tgt["priority"],[]),
                "timestamp_kst":  get_kst(),
                "ts_ms":          ts,
                "tgt_num":        tgt_num,
            })
    return detections

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# J7 화력 명령 패킷 빌더
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_j7_packet(tgt_num: str, weapon_id: int, unit_id: int,
                    rounds: int, lat: float, lon: float) -> bytes:
    def enc_lat(v): return int((v+90)/180*0xFFFFFFFF)
    def enc_lon(v): return int((v+180)/360*0xFFFFFFFF)
    tgt_b = tgt_num.encode()[:10].ljust(10, b"\x00")
    ts_ms = int(time.time()*1000)
    auth  = hmac.new(SECRET_KEY.encode(), tgt_b, hashlib.md5).digest()[:4]
    header = struct.pack(">2sIQ", b"KF", 1, ts_ms)
    data   = struct.pack(">10sBBBII4s",
        tgt_b, weapon_id, unit_id, rounds,
        enc_lat(lat), enc_lon(lon), auth)
    payload  = header + data
    checksum = sum(payload) & 0xFF
    return payload + struct.pack("B", checksum)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 활성 WebSocket 세션 관리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
active_drone_sessions: dict = {}
fire_mission_log: list = []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REST API 엔드포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/health")
async def health():
    return {"status":"ok","ts_kst":get_kst(),"model_loaded":model is not None}

@app.get("/api/targets/db")
async def get_target_db():
    return TARGET_DB

@app.get("/api/missions/log")
async def get_mission_log():
    return fire_mission_log[-50:]

@app.post("/api/fire-mission/approve")
async def approve_fire_mission(body: dict):
    det    = body.get("detection", {})
    tgt_num= det.get("tgt_num", "TGT-UNKNOWN")
    wpn    = det.get("weapon_recommendation", [{}])[0]
    lat    = body.get("lat", 37.5665)
    lon    = body.get("lon", 126.9780)
    packet = build_j7_packet(
        tgt_num, wpn.get("weapon_id",1),
        wpn.get("unit_id",10), 3, lat, lon
    )
    mission = {
        "tgt_num":      tgt_num,
        "timestamp_kst": get_kst(),
        "target_class": det.get("class","UNKNOWN"),
        "weapon":       wpn.get("weapon","N/A"),
        "unit":         wpn.get("unit","N/A"),
        "status":       "APPROVED",
        "j7_packet_hex": packet.hex(),
        "lat": lat, "lon": lon,
    }
    fire_mission_log.append(mission)
    return {"success":True,"mission":mission,"packet_bytes":len(packet)}

@app.get("/api/system/stats")
async def system_stats():
    return {
        "cpu_percent":    psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "active_drones":  len(active_drone_sessions),
        "missions_total": len(fire_mission_log),
        "ts_kst":         get_kst(),
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WebSocket — 드론 피드 스트리밍
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.websocket("/ws/drone/{drone_id}")
async def drone_websocket(websocket: WebSocket, drone_id: str):
    await websocket.accept()
    active_drone_sessions[drone_id] = websocket
    print(f"[카번개루스] 드론 연결: {drone_id}")

    # 데모 영상 경로
    video_src = DEMO_VIDEO if os.path.exists(DEMO_VIDEO) else 0
    cap = cv2.VideoCapture(video_src)
    seq = 0
    prev_det_hash = ""

    try:
        while cap.isOpened():
            t0 = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                await asyncio.sleep(0.1)
                continue

            # 해상도 축소 (레이턴시 최적화)
            small = cv2.resize(frame, (640, 360))

            # YOLOv8 추론
            dets = []
            if model:
                try:
                    results = model(small, conf=0.35, verbose=False)
                    dets = parse_detections(results, small.shape)
                except Exception as e:
                    print(f"[추론 오류] {e}")

            # 데모 모드: 실제 탐지 없으면 시뮬레이션 표적 주입
            if not dets:
                dets = _simulate_detections(seq)

            # 바운딩박스 오버레이
            annotated = _annotate_frame(small, dets)

            # JPEG 인코딩
            _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buf.tobytes()).decode()

            # 메시지 전송 (JSON — 프론트 호환성 우선)
            msg = {
                "seq":        seq,
                "ts_ms":      int(time.time() * 1000),
                "drone_id":   drone_id,
                "frame":      frame_b64,
                "detections": dets,
                "timestamp_kst": get_kst(),
            }
            await websocket.send_text(json.dumps(msg))
            seq += 1

            elapsed = (time.perf_counter() - t0) * 1000
            await asyncio.sleep(max(0.0, (100 - elapsed) / 1000))  # ~10fps

    except WebSocketDisconnect:
        print(f"[카번개루스] 드론 연결 해제: {drone_id}")
    except Exception as e:
        print(f"[카번개루스] 스트림 오류: {e}")
    finally:
        cap.release()
        active_drone_sessions.pop(drone_id, None)

def _simulate_detections(seq: int) -> list:
    """데모 모드: 실제 영상 없을 때 시뮬레이션 표적 생성"""
    import random
    if seq % 30 != 0:  # 3초마다 한 번
        return []
    classes  = ["2S19_MSTA_S", "M1978_Koksan", "BM21_Grad", "T72_series"]
    cls_name = random.choice(classes)
    tgt      = TARGET_DB.get(cls_name, TARGET_DB["T72_series"])
    x1,y1    = random.randint(50,400), random.randint(50,200)
    x2,y2    = x1+120, y1+80
    conf     = round(random.uniform(0.52, 0.95), 3)
    return [{
        "class":       cls_name,
        "confidence":  conf,
        "bbox":        [x1,y1,x2,y2],
        "center_px":   [(x1+x2)//2,(y1+y2)//2],
        "target_info":     tgt,
        "damage_radii":    calc_damage_radii(tgt["r0_m"]),
        "weapon_recommendation": WEAPON_MATRIX.get(tgt["priority"],[]),
        "timestamp_kst":   get_kst(),
        "ts_ms":           int(time.time()*1000),
        "tgt_num":         f"TGT-{datetime.now(KST).strftime('%H%M%S')}-SIM",
    }]

def _annotate_frame(frame: np.ndarray, dets: list) -> np.ndarray:
    COLORS = {"CRITICAL":(0,0,255),"HIGH":(0,128,255),"MEDIUM":(0,220,220),"LOW":(0,220,0)}
    for d in dets:
        x1,y1,x2,y2 = d["bbox"]
        pri   = d["target_info"].get("priority","LOW")
        color = COLORS.get(pri,(255,255,255))
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
        # 모서리 강조
        cl = 12
        for cx,cy,dx,dy in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
            cv2.line(frame,(cx,cy),(cx+dx*cl,cy),color,3)
            cv2.line(frame,(cx,cy),(cx,cy+dy*cl),color,3)
        label = f"{d['class']} {d['confidence']:.0%}"
        (tw,th),_ = cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.55,1)
        cv2.rectangle(frame,(x1,y1-22),(x1+tw+8,y1),color,-1)
        cv2.putText(frame,label,(x1+4,y1-6),cv2.FONT_HERSHEY_SIMPLEX,0.55,(255,255,255),1)
        wpn = d["weapon_recommendation"][0]["weapon"] if d["weapon_recommendation"] else ""
        cv2.putText(frame,f">{wpn}",(x1,y2+16),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,220,0),1)
    # HUD 오버레이
    cv2.putText(frame,f"KABORNERUS UAV FEED | {get_kst()}",(8,20),
                cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,220,100),1)
    cv2.putText(frame,f"TARGETS: {len(dets)}",(8,40),
                cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,220,100),1)
    return frame
