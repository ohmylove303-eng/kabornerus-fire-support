#!/usr/bin/env python3
"""
카번개루스 데모 드론 시뮬레이터
실제 드론 없이 WebSocket 백엔드에 모의 영상 + 탐지 데이터 전송

사용법:
  python demo_drone_simulator.py --drone-id KR-01 --fps 15
  python demo_drone_simulator.py --backend-url ws://localhost:8000 --drone-ids KR-01,KR-02
"""

import asyncio, argparse, time, math, random
import numpy as np
import cv2


def generate_demo_frame_with_bbox(
    frame_idx: int,
    width: int = 416,
    height: int = 234,
) -> tuple[np.ndarray, list[dict]]:
    """
    데모 프레임 생성: 위장색 배경 + 이동하는 표적 박스 시뮬레이션
    실제 드론 영상 없는 환경에서도 동작
    """
    # 배경: 녹색/갈색 지형 시뮬레이션
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (34, 60, 25)  # 어두운 녹색 기본

    # 지형 노이즈
    noise = np.random.randint(0, 20, (height, width, 3), dtype=np.uint8)
    frame = cv2.add(frame, noise)

    detections = []
    t = frame_idx * 0.05

    # 표적 1: 이동하는 차량 (2S19 시뮬레이션)
    if frame_idx % 90 < 70:  # 70/90 프레임 동안 출현
        x_center = int(width * 0.3 + 40 * math.sin(t))
        y_center = int(height * 0.5 + 20 * math.cos(t * 0.7))
        bw, bh = 55, 30

        # 차량 외형 그리기 (직사각형 + 포신)
        cv2.rectangle(frame,
                      (x_center - bw//2, y_center - bh//2),
                      (x_center + bw//2, y_center + bh//2),
                      (80, 110, 60), -1)
        cv2.rectangle(frame,
                      (x_center - bw//2, y_center - bh//2),
                      (x_center + bw//2, y_center + bh//2),
                      (120, 150, 90), 2)
        # 포신
        cv2.line(frame,
                 (x_center, y_center),
                 (x_center + bw, y_center - 5),
                 (100, 130, 70), 3)

        conf = 0.72 + 0.15 * random.random()
        detections.append({
            "class":      "2S19_MSTA",
            "confidence": round(conf, 3),
            "bbox":       [x_center - bw//2, y_center - bh//2,
                           x_center + bw//2, y_center + bh//2],
        })

    # 표적 2: 정지 차량 (T-72 시뮬레이션)
    if frame_idx % 120 > 30:
        x2, y2 = int(width * 0.7), int(height * 0.35)
        bw2, bh2 = 48, 28
        cv2.rectangle(frame,
                      (x2 - bw2//2, y2 - bh2//2),
                      (x2 + bw2//2, y2 + bh2//2),
                      (60, 80, 50), -1)
        conf2 = 0.65 + 0.20 * random.random()
        detections.append({
            "class":      "T72_series",
            "confidence": round(conf2, 3),
            "bbox":       [x2 - bw2//2, y2 - bh2//2,
                           x2 + bw2//2, y2 + bh2//2],
        })

    return frame, detections


async def simulate_drone(
    drone_id: str,
    backend_url: str,
    fps: int = 15,
):
    """백엔드 WebSocket에 모의 드론 데이터 스트림 전송"""
    import websockets, msgpack, struct

    ws_url = f"{backend_url}/ws/drone-feed/{drone_id}"
    print(f"[{drone_id}] 연결 시도: {ws_url}")

    frame_interval = 1.0 / fps

    async with websockets.connect(ws_url) as ws:
        print(f"[{drone_id}] 연결 성공 ({fps}fps)")
        frame_idx = 0

        while True:
            t_start = time.perf_counter()

            frame, dets = generate_demo_frame_with_bbox(frame_idx)
            _, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, 60])
            jpeg_bytes = buf.tobytes()
            det_bytes  = msgpack.packb(dets, use_bin_type=True)

            # KR 패킷 조립
            header = struct.pack(
                ">2sIQHI",
                b"KR", frame_idx,
                int(time.time() * 1000),
                len(det_bytes), len(jpeg_bytes)
            )
            packet = header + det_bytes + jpeg_bytes

            try:
                await ws.send(packet)
            except Exception as e:
                print(f"[{drone_id}] 전송 오류: {e}")
                break

            frame_idx += 1
            elapsed = time.perf_counter() - t_start
            await asyncio.sleep(max(0.0, frame_interval - elapsed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--drone-id",    default="KR-01")
    parser.add_argument("--drone-ids",   default="")
    parser.add_argument("--backend-url", default="ws://localhost:8000")
    parser.add_argument("--fps",         type=int, default=15)
    args = parser.parse_args()

    drone_ids = (
        args.drone_ids.split(",")
        if args.drone_ids
        else [args.drone_id]
    )

    async def main():
        await asyncio.gather(*[
            simulate_drone(did, args.backend_url, args.fps)
            for did in drone_ids
        ])

    asyncio.run(main())
