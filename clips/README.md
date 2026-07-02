# UAV 클립 파이프라인 사용법

## 빠른 시작

```bash
# 1. 의존성 설치
pip install yt-dlp opencv-python numpy
brew install ffmpeg

# 2. 실행 (자동 다운로드 + 슬라이싱 + UAV 변환)
cd clips
python uav_clip_pipeline.py

# 3. 결과물 확인
open output/  # macOS Finder
```

## 출력 파일 구조
```
clips/
├── raw/          # 원본 다운로드 + 슬라이싱 캐시
├── output/       # 최종 검증용 클립 (640x360, 4~5초)
│   ├── NK_SPH_Koksan_FPV_Donetsk_2025.mp4   ← 경로 A (실제 FPV)
│   ├── NK_SPH_Koksan_Luhansk_First_2025.mp4  ← 경로 A (실제 드론)
│   ├── NK_MRL_KN25_Firing_2024.mp4           ← 경로 B (UAV 변환)
│   ├── NK_MBT_Chonma20_Parade_2025.mp4       ← 경로 B (UAV 변환)
│   └── NK_SPH_155mm_Factory_2026.mp4         ← 경로 B (UAV 변환)
└── OSINT_VIDEO_SOURCES.md  # 소스 목록
```

## 클래스 정의
| 클래스 | 설명 |
|---|---|
| NK_SPH_KOKSAN | 북한 M1978 Koksan 170mm 자주포 |
| NK_SPH_155MM | 북한 신형 155mm 자주포 (2026) |
| NK_MRL_KN25 | 북한 KN-25 초대형방사포 600mm |
| NK_MBT_CHONMA20 | 북한 천마-20 전차 |

## yt-dlp 실패 시 수동 대체
militarnyi.com / nv.ua 영상은 페이지에서 직접 mp4 URL 추출:
```bash
yt-dlp --get-url <페이지URL>
# 또는 브라우저 F12 → Network → mp4 필터
```
