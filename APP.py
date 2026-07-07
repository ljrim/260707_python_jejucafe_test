# -*- coding: utf-8 -*-
"""
제주도 카페 상권분석 보고서
- 데이터: jeju_cafe.csv (카페 상가), jeju_dong_stats.csv (행정동별 전체 상가 수)
  * 원본(제주상권.csv, cp949, 21MB)에서 배포용으로 경량화(UTF-8, 약 0.5MB)
- 실행: streamlit run APP.py
"""

import os
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(
    page_title="제주도 카페 상권분석 보고서",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAFE_PATH = os.path.join(BASE_DIR, "jeju_cafe.csv")
STATS_PATH = os.path.join(BASE_DIR, "jeju_dong_stats.csv")


# ------------------------------------------------------------------
# 데이터 로드
# ------------------------------------------------------------------
@st.cache_data(show_spinner="데이터를 불러오는 중입니다...")
def load_cafe(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    for col in ["경도", "위도"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_stats(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


for p in (CAFE_PATH, STATS_PATH):
    if not os.path.exists(p):
        st.error(f"데이터 파일을 찾을 수 없습니다: {p}")
        st.stop()

df_cafe = load_cafe(CAFE_PATH)
df_stats = load_stats(STATS_PATH)

# ------------------------------------------------------------------
# 사이드바 필터
# ------------------------------------------------------------------
st.sidebar.title("☕ 필터")
st.sidebar.caption("분석 대상 지역을 선택하세요.")

sigungu_options = ["전체"] + sorted(df_cafe["시군구명"].dropna().unique().tolist())
sel_sigungu = st.sidebar.selectbox("시·군·구", sigungu_options, index=0)

if sel_sigungu == "전체":
    base_cafe = df_cafe
    base_stats = df_stats
else:
    base_cafe = df_cafe[df_cafe["시군구명"] == sel_sigungu]
    base_stats = df_stats[df_stats["시군구명"] == sel_sigungu]

dong_all = sorted(base_cafe["행정동명"].dropna().unique().tolist())
sel_dong = st.sidebar.multiselect("행정동 (미선택 시 전체)", dong_all, default=[])

if sel_dong:
    f_cafe = base_cafe[base_cafe["행정동명"].isin(sel_dong)]
    f_stats = base_stats[base_stats["행정동명"].isin(sel_dong)]
else:
    f_cafe = base_cafe
    f_stats = base_stats

st.sidebar.divider()
st.sidebar.metric("선택 지역 카페 수", f"{len(f_cafe):,} 개")
st.sidebar.caption(
    "출처 형식: 소상공인시장진흥공단 상가(상권)정보\n\n"
    "카페 = 상권업종소분류 '카페'"
)

# ------------------------------------------------------------------
# 헤더
# ------------------------------------------------------------------
st.title("☕ 제주도 카페 상권분석 보고서")
st.markdown(
    "제주특별자치도의 상가업소 데이터를 기반으로 **카페 업종의 분포·밀집도·상권 특성**을 분석합니다."
)

region_label = "제주 전역" if sel_sigungu == "전체" else sel_sigungu
if sel_dong:
    region_label += f" · {', '.join(sel_dong[:3])}" + (" 외" if len(sel_dong) > 3 else "")
st.caption(f"현재 분석 범위: **{region_label}**")

# ------------------------------------------------------------------
# KPI 지표
# ------------------------------------------------------------------
total_cafe = len(f_cafe)
total_biz = int(f_stats["전체상가수"].sum())
cafe_share = (total_cafe / total_biz * 100) if total_biz else 0
n_dong = f_cafe["행정동명"].nunique()

if total_cafe > 0:
    top_dong = f_cafe["행정동명"].value_counts().idxmax()
    top_dong_cnt = int(f_cafe["행정동명"].value_counts().max())
else:
    top_dong, top_dong_cnt = "-", 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 카페 수", f"{total_cafe:,} 개")
c2.metric("전체 상가 대비 비율", f"{cafe_share:.1f} %", help="선택 지역 전체 상가 중 카페가 차지하는 비중")
c3.metric("카페 분포 행정동 수", f"{n_dong:,} 곳")
c4.metric("카페 최다 행정동", top_dong, f"{top_dong_cnt:,} 개")

st.divider()

# ------------------------------------------------------------------
# 탭 구성
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📍 지역별 분포", "🗺️ 밀집도 지도", "📊 상권 특성", "📋 데이터 조회"]
)

# ------------------------------------------------------------------
# 탭1: 지역별 분포
# ------------------------------------------------------------------
with tab1:
    st.subheader("시·군·구별 카페 분포")
    col_a, col_b = st.columns([1, 1.4])

    with col_a:
        by_sigungu = (
            df_cafe["시군구명"].value_counts().rename_axis("시군구").reset_index(name="카페수")
        )
        fig_pie = px.pie(
            by_sigungu, names="시군구", values="카페수", hole=0.45,
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        fig_pie.update_traces(textinfo="label+percent", textposition="inside")
        fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=340)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("제주 전역 기준 시·군·구 비중")

    with col_b:
        st.markdown("**행정동별 카페 수 TOP 15**")
        topn = (
            f_cafe["행정동명"].value_counts().head(15)
            .rename_axis("행정동").reset_index(name="카페수")
            .sort_values("카페수")
        )
        fig_bar = px.bar(
            topn, x="카페수", y="행정동", orientation="h",
            color="카페수", color_continuous_scale="Teal", text="카페수",
        )
        fig_bar.update_layout(
            coloraxis_showscale=False, margin=dict(t=10, b=10, l=10, r=10),
            height=460, yaxis_title="", xaxis_title="카페 수",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.info(
        f"💡 선택 범위에서 카페가 가장 많은 행정동은 **{top_dong}**({top_dong_cnt:,}개)이며, "
        "카페 창업/상권 진입 시 이미 경쟁이 치열한 성숙 상권으로 해석할 수 있습니다."
    )

# ------------------------------------------------------------------
# 탭2: 밀집도 지도
# ------------------------------------------------------------------
with tab2:
    st.subheader("카페 밀집도 지도")
    map_df = f_cafe.dropna(subset=["경도", "위도"]).copy()
    map_df = map_df[(map_df["위도"].between(33.0, 34.1)) & (map_df["경도"].between(126.0, 127.0))]

    if map_df.empty:
        st.warning("표시할 좌표 데이터가 없습니다.")
    else:
        view_mode = st.radio(
            "지도 표현 방식", ["밀집도(Hexagon)", "개별 위치(Point)"], horizontal=True
        )
        view_state = pdk.ViewState(
            latitude=float(map_df["위도"].mean()),
            longitude=float(map_df["경도"].mean()),
            zoom=9.3, pitch=45,
        )

        if view_mode.startswith("밀집도"):
            layer = pdk.Layer(
                "HexagonLayer",
                data=map_df[["경도", "위도"]],
                get_position="[경도, 위도]",
                radius=350, elevation_scale=6, elevation_range=[0, 1500],
                extruded=True, coverage=0.9, pickable=True,
            )
            tooltip = {"text": "이 구역 카페 수: {elevationValue}"}
        else:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df[["경도", "위도", "상호명", "행정동명"]],
                get_position="[경도, 위도]",
                get_fill_color=[0, 140, 140, 140], get_radius=60, pickable=True,
            )
            tooltip = {"text": "{상호명}\n{행정동명}"}

        st.pydeck_chart(
            pdk.Deck(map_style=None, initial_view_state=view_state,
                     layers=[layer], tooltip=tooltip)
        )
        st.caption(
            "막대(기둥)가 높고 붉을수록 카페가 밀집된 상권입니다. "
            "관광 중심지·번화가에 집중되는 경향을 확인할 수 있습니다."
        )

# ------------------------------------------------------------------
# 탭3: 상권 특성 — 카페 특화도
# ------------------------------------------------------------------
with tab3:
    st.subheader("행정동별 카페 특화 상권 분석")
    st.markdown(
        "각 행정동에서 **전체 상가 중 카페가 차지하는 비율(카페 특화도)** 을 계산하여, "
        "단순 개수가 아닌 '카페 중심 상권'을 발굴합니다."
    )

    min_biz = st.slider(
        "최소 카페 수 (분석 대상 행정동 기준)", 1, 50, 10,
        help="표본이 너무 적은 행정동을 제외해 왜곡을 줄입니다.",
    )

    cafe_by_dong = base_cafe["행정동명"].value_counts().rename("카페수")
    all_by_dong = base_stats.groupby("행정동명")["전체상가수"].sum().rename("전체상가수")
    merged = pd.concat([cafe_by_dong, all_by_dong], axis=1).dropna()
    merged["카페비율(%)"] = (merged["카페수"] / merged["전체상가수"] * 100).round(1)
    merged = merged[merged["카페수"] >= min_biz].reset_index(names="행정동")

    if merged.empty:
        st.warning("조건을 만족하는 행정동이 없습니다. 최소 카페 수를 낮춰 보세요.")
    else:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**카페 특화도 TOP 10** (카페비율 높은 순)")
            sp = merged.sort_values("카페비율(%)", ascending=False).head(10).sort_values("카페비율(%)")
            fig_sp = px.bar(
                sp, x="카페비율(%)", y="행정동", orientation="h",
                color="카페비율(%)", color_continuous_scale="Sunsetdark", text="카페비율(%)",
            )
            fig_sp.update_layout(
                coloraxis_showscale=False, height=420, margin=dict(t=10, b=10, l=10, r=10),
                yaxis_title="", xaxis_title="카페 비율(%)",
            )
            st.plotly_chart(fig_sp, use_container_width=True)

        with col_r:
            st.markdown("**카페 수 vs 카페 비율** (상권 규모·특화도 동시 비교)")
            fig_sc = px.scatter(
                merged, x="전체상가수", y="카페비율(%)", size="카페수",
                hover_name="행정동", color="카페수", color_continuous_scale="Teal", size_max=40,
            )
            fig_sc.update_layout(
                height=420, margin=dict(t=10, b=10, l=10, r=10),
                xaxis_title="전체 상가 수(상권 규모)", yaxis_title="카페 비율(%)",
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        st.markdown("**행정동별 상세 지표**")
        st.dataframe(
            merged.sort_values("카페비율(%)", ascending=False).reset_index(drop=True),
            use_container_width=True, height=300,
        )
        st.info(
            "💡 **카페 수는 적지만 비율이 높은 행정동**은 관광지형·특화 상권일 가능성이 높고, "
            "**규모가 크면서 비율도 높은 행정동**은 카페 격전지입니다. "
            "산점도 우상단이 '큰 상권 + 높은 카페 밀도'에 해당합니다."
        )

# ------------------------------------------------------------------
# 탭4: 데이터 조회
# ------------------------------------------------------------------
with tab4:
    st.subheader("카페 원본 데이터 조회")
    kw = st.text_input("상호명 검색", placeholder="예: 스타벅스, 카페")
    view_cols = [
        "상호명", "상권업종소분류명", "시군구명", "행정동명",
        "지번주소", "도로명주소", "경도", "위도",
    ]
    show = f_cafe[view_cols].copy()
    if kw:
        show = show[show["상호명"].astype(str).str.contains(kw, case=False, na=False)]

    st.caption(f"조회 결과: {len(show):,} 건")
    st.dataframe(show.reset_index(drop=True), use_container_width=True, height=440)

    csv_bytes = show.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ 현재 결과 CSV 다운로드",
        data=csv_bytes,
        file_name="제주_카페_상권분석.csv",
        mime="text/csv",
    )

st.divider()
st.caption("© 제주도 카페 상권분석 보고서 · 데이터: jeju_cafe.csv · Powered by Streamlit")
