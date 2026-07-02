#!/usr/bin/env python3
"""
UAV 시점 영상 슬라이서 + 원근변환 파이프라인
경로 A: 실제 FPV 드론 영상 → 4~5초 직접 슬라이싱
경로 B: 지상 촬영 영상 → UAV Dive 시점 변환 → 슬라이싱

Requirements:
    pip install yt-dlp opencv-python numpy
    brew install ffmpeg  # macOS
"""

import subprocess
import os
import cv2
import numpy as np
from pathlib import Path

OUT_DIR = Path("clips/output")
RAW_DIR = Path("clips/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# 소스 정의
# ─────────────────────────────────────────
CLIPS = [
    # ── 경로 A: 실제 FPV/드론 시점 (변환 불필요) ──
    {
        "label": "NK_SPH_Koksan_FPV_Donetsk_2025",
        "url": "https://militarnyi.com/en/news/ukrainian-military-hits-north-korean-koksan-self-propelled-gun-in-donetsk-region/",
        "start": "00:00:00",
        "duration": "5",
        "class": "NK_SPH_KOKSAN",
        "mode": "A",  # 직접 슬라이싱
    },
    {
        "label": "NK_SPH_Koksan_Luhansk_First_2025",
        "url": "https://english.nv.ua/nation/first-confirmed-loss-of-north-korean-howitzer-koksan-video-50491115.html",
        "start": "00:00:00",
        "duration": "5",
        "class": "NK_SPH_KOKSAN",
        "mode": "A",
    },
    # ── 경로 B: 지상 시점 → UAV 변환 ──
    {
        "label": "NK_MRL_KN25_Firing_2024",
        "url": "https://www.youtube.com/watch?v=0nt3YAKOttk",
        "start": "00:00:03",
        "duration": "5",
        "class": "NK_MRL_KN25",
        "mode": "B",  # UAV 시점 변환 적용
    },
    {
        "label": "NK_MBT_Chonma20_Parade_2025",
        "url": "https://www.youtube.com/watch?v=qzmmv-SWMRE",
        "start": "00:02:17",
        "duration": "5",
        "class": "NK_MBT_CHONMA20",
        "mode": "B",
    },
    {
        "label": "NK_SPH_155mm_Factory_2026",
        "url": "https://www.youtube.com/watch?v=2libstC7OgI",
        "start": "00:00:05",
        "duration": "4",
        "class": "NK_SPH_155MM",
        "mode": "B",
    },
]


# ─────────────────────────────────────────
# 경로 B: UAV Dive 시점 변환
# ─────────────────────────────────────────
def simulate_uav_dive(frame: np.ndarray, dive_progress: float) -> np.ndarray:
    """
    dive_progress: 0.0(고고도 탑뷰) → 1.0(근접 Dive)
    """
    h, w = frame.shape[:2]

    # 1) 탑다운 원근 변환 (사다리꼴 → 직사각형)
    squeeze = int(w * 0.20 * (1.0 - dive_progress * 0.5))
    pts_src = np.float32([[squeeze, 0], [w - squeeze, 0], [0, h], [w, h]])
    pts_dst = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    warped = cv2.warpPerspective(frame, M, (w, h))

    # 2) 줌인 (Dive 접근 시뮬레이션)
    zoom = 1.0 + dive_progress * 2.5  # 최대 3.5x
    cx, cy = w // 2, h // 2
    new_w = int(w / zoom)
    new_h = int(h / zoom)
    x1 = max(cx - new_w // 2, 0)
    y1 = max(cy - new_h // 2, 0)
    x2 = min(cx + new_w // 2, w)
    y2 = min(cy + new_h // 2, h)
    cropped = warped[y1:y2, x1:x2]
    result = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    # 3) 열화상 느낌 색조 (선택사항 — UAV EO/IR 느낌)
    # result = cv2.applyColorMap(cv2.cvtColor(result, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_INFERNO)

    return result


def apply_uav_transform(raw_path: str, out_path: str):
    cap = cv2.VideoCapture(raw_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (640, 360))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        progress = frame_idx / max(total_frames - 1, 1)  # 0.0 → 1.0
        transformed = simulate_uav_dive(frame, progress)
        resized = cv2.resize(transformed, (640, 360))
        writer.write(resized)
        frame_idx += 1

    cap.release()
    writer.release()
    print(f"  [변환 완료] {out_path}")


# ─────────────────────────────────────────
# 공통: yt-dlp 다운로드 + ffmpeg 슬라이싱
# ─────────────────────────────────────────
def download_and_slice(clip: dict):
    label = clip["label"]
    raw_path = str(RAW_DIR / f"{label}_raw.mp4")
    sliced_path = str(RAW_DIR / f"{label}_sliced.mp4")
    final_path = str(OUT_DIR / f"{label}.mp4")

    print(f"\n[{clip['mode']}] {label} 처리 시작")

    # 1) 다운로드
    if not os.path.exists(raw_path):
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo/best",
                "--merge-output-format", "mp4",
                "--output", raw_path,
                clip["url"],
            ],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  [경고] yt-dlp 실패: {result.stderr[:200]}")
            print(f"  → 수동 다운로드 후 {raw_path} 에 저장하세요")
            return None
        print(f"  [다운로드 완료] {raw_path}")
    else:
        print(f"  [캐시 사용] {raw_path}")

    # 2) ffmpeg 슬라이싱 (4~5초)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", clip["start"],
            "-i", raw_path,
            "-t", clip["duration"],
            "-vf", "scale=640:360",
            "-c:v", "libx264", "-an",
            sliced_path,
        ],
        capture_output=True
    )
    print(f"  [슬라이싱 완료] {sliced_path}")

    # 3) 경로 B: UAV 시점 변환
    if clip["mode"] == "B":
        apply_uav_transform(sliced_path, final_path)
    else:
        # 경로 A: 그대로 복사
        import shutil
        shutil.copy(sliced_path, final_path)
        print(f"  [직접 사용] {final_path}")

    return final_path


# ─────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("="*50)
    print("카번개루스 UAV 클립 파이프라인")
    print("="*50)

    results = []
    for clip in CLIPS:
        path = download_and_slice(clip)
        if path:
            results.append({"label": clip["label"], "class": clip["class"], "path": path})

    print("\n" + "="*50)
    print("완료된 클립:")
    for r in results:
        print(f"  [{r['class']}] {r['path']}")
    print("\n→ clips/output/ 폴더에서 검증하세요")
