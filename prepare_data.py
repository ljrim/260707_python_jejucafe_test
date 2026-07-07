# -*- coding: utf-8 -*-
"""
원본 제주상권.csv(cp949, 약 21MB)를 배포용 경량 CSV로 변환하는 스크립트.
새 원본을 받았을 때만 한 번 실행하면 됩니다.

    python prepare_data.py

생성물:
    - jeju_cafe.csv        : 카페 상가 (필요 컬럼만, UTF-8, 약 0.5MB)
    - jeju_dong_stats.csv  : 행정동별 전체 상가 수 (카페 비율 계산용 분모)
"""

import pandas as pd

SRC = "제주상권.csv"

df = pd.read_csv(SRC, encoding="cp949", low_memory=False)

# 1) 카페 원본 (필요 컬럼만)
cols = ["상호명", "상권업종소분류명", "시군구명", "행정동명",
        "지번주소", "도로명주소", "경도", "위도"]
cafe = df[df["상권업종소분류명"] == "카페"][cols].copy()
for c in ["경도", "위도"]:
    cafe[c] = pd.to_numeric(cafe[c], errors="coerce").round(6)
cafe.to_csv("jeju_cafe.csv", index=False, encoding="utf-8-sig")

# 2) 행정동별 전체 상가 수 (비율 계산 분모)
stats = df.groupby(["시군구명", "행정동명"]).size().reset_index(name="전체상가수")
stats.to_csv("jeju_dong_stats.csv", index=False, encoding="utf-8-sig")

print(f"jeju_cafe.csv       : {len(cafe):,} rows")
print(f"jeju_dong_stats.csv : {len(stats):,} rows")
print("완료")
