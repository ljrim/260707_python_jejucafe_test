# ☕ 제주도 카페 상권분석 보고서

제주특별자치도 상가업소 데이터를 기반으로 **카페 업종의 분포·밀집도·상권 특성**을 분석하는 Streamlit 대시보드입니다.

## 주요 기능
- **KPI 요약** — 총 카페 수, 전체 상가 대비 비율, 분포 행정동 수, 카페 최다 행정동
- **📍 지역별 분포** — 시·군·구 비중(도넛), 행정동 TOP 15 카페 수
- **🗺️ 밀집도 지도** — pydeck 기반 밀집도(Hexagon) / 개별 위치(Point) 지도
- **📊 상권 특성** — 행정동별 '카페 특화도(카페÷전체 상가)'로 카페 중심 상권 발굴
- **📋 데이터 조회** — 상호명 검색 및 CSV 다운로드

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run APP.py
```
브라우저에서 http://localhost:8501 접속

## 데이터
| 파일 | 설명 |
|------|------|
| `jeju_cafe.csv` | 카페 상가 (필요 컬럼만, UTF-8, 약 0.5MB) |
| `jeju_dong_stats.csv` | 행정동별 전체 상가 수 (카페 비율 계산용 분모) |
| `prepare_data.py` | 원본 `제주상권.csv`(cp949, 약 21MB) → 경량 CSV 변환 스크립트 |

> 원본 `제주상권.csv`는 용량이 커서 배포에서 제외(.gitignore)합니다.
> 새 원본을 받으면 `python prepare_data.py`로 경량 CSV를 다시 생성하세요.
> 출처 형식: 소상공인시장진흥공단 상가(상권)정보.

## Streamlit Community Cloud 배포
1. 이 폴더를 GitHub 저장소에 push (원본 CSV는 자동 제외됨)
2. https://share.streamlit.io → **New app**
3. 저장소 선택, **Main file path** = `APP.py` 지정 후 **Deploy**
