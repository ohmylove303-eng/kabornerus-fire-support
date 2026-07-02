# UAV 시점 검증용 OSINT 영상 소스 목록

> 상공→지상 Dive 시점, 4~5초 슬라이싱 대상

## 1. 북한 자주포 (SPH)

| # | 레이블 | URL | 타임스탬프 | 클래스 | 시점 |
|---|---|---|---|---|---|
| 1 | NK_SPH_Koksan_FPV_Donetsk_2025 | https://militarnyi.com/en/news/ukrainian-military-hits-north-korean-koksan-self-propelled-gun-in-donetsk-region/ | 전체 | NK_SPH_KOKSAN | ✅ FPV Dive 실제 |
| 2 | NK_SPH_Koksan_Luhansk_First_2025 | https://english.nv.ua/nation/first-confirmed-loss-of-north-korean-howitzer-koksan-video-50491115.html | 전체 | NK_SPH_KOKSAN | ✅ 드론 탑뷰 |
| 3 | NK_SPH_155mm_Factory_2026 | https://www.youtube.com/watch?v=2libstC7OgI | 00:00:05 ~ 00:00:10 | NK_SPH_155MM | ⚠️ 지상시점→변환필요 |
| 4 | NK_SPH_155mm_ChannelA_2026 | https://www.youtube.com/watch?v=n2GE7BKvjTA | 00:00:00 ~ 00:00:07 | NK_SPH_155MM | ⚠️ 지상시점→변환필요 |

## 2. 북한 방사포 (MRL)

| # | 레이블 | URL | 타임스탬프 | 클래스 | 시점 |
|---|---|---|---|---|---|
| 5 | NK_MRL_KN25_Firing_2024 | https://www.youtube.com/watch?v=0nt3YAKOttk | 00:00:03 ~ 00:00:08 | NK_MRL_KN25 | ⚠️ 지상시점→변환필요 |
| 6 | NK_MRL_BBC_Drill | https://www.bbc.com/news/av/world-asia-64696247 | 전체 루프 | NK_MRL_MLRS | ⚠️ 지상시점→변환필요 |

## 3. 북한 전차 (MBT)

| # | 레이블 | URL | 타임스탬프 | 클래스 | 시점 |
|---|---|---|---|---|---|
| 7 | NK_MBT_Chonma20_Parade_2025 | https://www.youtube.com/watch?v=qzmmv-SWMRE | 00:02:17 ~ 00:02:22 | NK_MBT_CHONMA20 | ⚠️ 지상시점→변환필요 |

## 시점 범례
- ✅ FPV Dive 실제: 추가 편집 없이 즉시 사용 가능
- ⚠️ 지상시점→변환필요: `uav_clip_pipeline.py` B경로 적용
