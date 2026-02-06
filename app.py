import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# =================================================================
# 1. 페이지 설정 및 전역 변수 (기능 절대 보존)
# =================================================================
st.set_page_config(
    page_title="남이천1센터 물동량 통합 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로고 및 경로 설정
LOGO_PATH = "LOGO"
BG_IMAGE_FILE = os.path.join(LOGO_PATH, "센터조감도.png")
MAIN_LOGO_FILE = os.path.join(LOGO_PATH, "한익스_LOGO.png")

# 화주사 로고 매핑 리스트 (절대 누락 금지)
LOGO_MAP = {
    "DKSH L&L": "DKSH L&L_LOGO.png", "대호 F&B": "대호 F&B_LOGO.png", "덴비코리아": "덴비_LOGO.png",
    "막시무스코리아": "막시무스코리아.png", "매그니프": "매그니프_LOGO.png", "멘소래담": "멘소래담_LOGO.png",
    "머거본": "머거본_LOGO.png", "바이오포트코리아": "바이오포트코리아_LOGO.png", "시세이도": "시세이도_LOGO.png",
    "유니레버": "유니레버_LOGO.png", "커머스파크": "커머스파크_LOGO.png", "펄세스": "펄세스_LOGO.png",
    "PRODENTI": "프로덴티_LOGO.png", "한국프리오": "한국프리오_LOGO.png", "헨켈홈케어": "헨켈홈케어_LOGO.png",
    "네이처리퍼블릭": "네이처리퍼블릭_LOGO.png"
}

# =================================================================
# 2. 데이터 및 이미지 처리 엔진 (영진님 0점 처리 반영)
# =================================================================
def get_image_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def clean_value_to_float(v):
    """영진님이 0으로 채우신 데이터를 가장 안전하게 읽어오는 로직"""
    if pd.isna(v) or str(v).strip() in ["", "-", "None", "nan"]: return 0.0
    try:
        s = str(v).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

@st.cache_data(ttl=1)
def fetch_master_data(sheet_name):
    """구글 시트 헤더 정밀 감지 및 데이터 로드 로직 (보존)"""
    try:
        sid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        raw_df = pd.read_csv(url, header=None, dtype=str)
        h_idx = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values: h_idx = i; break
        df = raw_df.iloc[h_idx+1:].copy()
        df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(raw_df.iloc[h_idx])]
        df = df.dropna(subset=['화주사', '구분'])
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '').str.upper()
        return df
    except: return pd.DataFrame()

# =================================================================
# 3. 강화된 디자인 CSS (홈 화면 업그레이드 요소 포함)
# =================================================================
bg_b64 = get_image_b64(BG_IMAGE_FILE)
st.markdown(f"""
<style>
    /* 전체 배경 스타일 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{bg_b64}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    /* 홈 로고 투명 버튼 */
    .home-btn-container {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important; color: transparent !important; z-index: 100 !important;
    }}
    /* 업그레이드된 KPI 카드 디자인 */
    .kpi-card {{
        background-color: white; padding: 25px; border-radius: 15px; border-left: 6px solid #002D56;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: left; transition: 0.3s;
    }}
    .kpi-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
    .kpi-title {{ font-size: 1.1rem; color: #666; font-weight: 600; }}
    .kpi-value {{ font-size: 2.5rem; color: #002D56; font-weight: 800; margin-top: 10px; }}
    
    /* 전광판 배너 스타일 */
    .main-banner {{
        background: linear-gradient(135deg, #002D56 0%, #0056b3 100%);
        color: white; padding: 40px; border-radius: 20px; text-align: center; margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,45,86,0.3);
    }}
    /* 로고 슬라이더 (보존) */
    @keyframes scroll_logo {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider-box {{ background: white; height: 100px; margin-bottom: 30px; overflow: hidden; position: relative; border-radius: 12px; display: flex; align-items: center; }}
    .slider-track {{ animation: scroll_logo 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide-item {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slide-item img {{ max-height: 70px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# 데이터 로드
df_v = fetch_master_data('구글 데이터')
df_t = fetch_master_data('임시직')

if not df_v.empty:
    clist = list(dict.fromkeys(df_v['화주사'].tolist()))
    if 'vmode' not in st.session_state: st.session_state.vmode = 'home'
    if 'scomp' not in st.session_state: st.session_state.scomp = clist[0]

    with st.sidebar:
        st.markdown('<div class="home-btn-container">', unsafe_allow_html=True)
        if st.button("HOME_ACTION"): st.session_state.vmode = 'home'; st.rerun()
        if os.path.exists(MAIN_LOGO_FILE): st.image(MAIN_LOGO_FILE, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        c_idx = clist.index(st.session_state.scomp) if st.session_state.scomp in clist else 0
        sel = st.radio("📍 화주사 리스트", clist, index=c_idx if st.session_state.vmode == 'detail' else None)
        if sel: st.session_state.vmode = 'detail'; st.session_state.scomp = sel
            
        target_month = st.selectbox("📅 월 선택", [f"{i:02d}" for i in range(1, 13)])
        date_cols = [c for c in df_v.columns if re.search(r'^\d{1,2}$', str(c).strip())]

    # =================================================================
    # 4. 메인 화면 - [HOME 페이지: 디자인 강화 버전]
    # =================================================================
    if st.session_state.vmode == 'home':
        # 상단 전광판
        st.markdown(f"""<div class="main-banner">
            <h1 style="color: #FFD700; margin: 0; font-size: 3.2rem;">{target_month}월 남이천1센터 종합 지표</h1>
            <p style="margin-top: 10px; opacity: 0.9; font-size: 1.2rem;">HANEX Logistics 실시간 물동량 현황 모니터링</p>
        </div>""", unsafe_allow_html=True)

        # 요약 데이터 집계
        summary_list = []
        for c in clist:
            mk = c.replace(' ', '').upper()
            v_val = df_v[df_v['match_name'] == mk][date_cols].applymap(clean_value_to_float).sum().sum()
            t_val = 0
            if not df_t.empty:
                t_sub = df_t[df_t['match_name'] == mk]
                at_cols = [tc for tc in date_cols if tc in t_sub.columns]
                t_val = t_sub[at_cols].applymap(clean_value_to_float).sum().sum() if at_cols else 0
            summary_list.append({"화주사": c, "물동량": v_val, "인원": t_val})
        
        sdf = pd.DataFrame(summary_list)
        total_vol = sdf['물동량'].sum()
        total_tmp = sdf['인원'].sum()
        prod = total_vol / total_tmp if total_tmp > 0 else 0

        # KPI 카드 3분할 배치
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">📦 총 물동량</div><div class="kpi-value">{int(total_vol):,}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-card" style="border-left-color: #FFD700;"><div class="kpi-title">👤 투입 인원</div><div class="kpi-value">{int(total_tmp):,}명</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-card" style="border-left-color: #28a745;"><div class="kpi-title">⚡ 평균 생산성</div><div class="kpi-value">{prod:.1f}</div></div>', unsafe_allow_html=True)

        st.write("###") # 여백

        # 차트 및 순위표
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("#### 📈 화주사별 물동량 비중")
            st.bar_chart(sdf.set_index('화주사')['물동량'], color="#002D56")
        with c2:
            st.markdown("#### 📋 실적 TOP 10")
            rank_df = sdf.sort_values('물동량', ascending=False).head(10).copy()
            rank_df['물동량'] = rank_df['물동량'].apply(lambda x: f"{int(x):,}")
            st.dataframe(rank_df[['화주사', '물동량']], use_container_width=True, hide_index=True)

        # 로고 슬라이더 (보존)
        slides_html = "".join([f'<div class="slide-item"><img src="data:image/png;base64,{get_image_b64(os.path.join(LOGO_PATH, f))}"></div>' for n, f in LOGO_MAP.items() if get_image_b64(os.path.join(LOGO_PATH, f))])
        st.markdown(f'<div class="slider-box"><div class="slider-track">{slides_html}</div></div>', unsafe_allow_html=True)

    # =================================================================
    # 5. 메인 화면 - [상세 페이지: 기존 음영 서식 100% 보존]
    # =================================================================
    else:
        target = st.session_state.scomp
        if target in LOGO_MAP:
            l_b64 = get_image_b64(os.path.join(LOGO_PATH, LOGO_MAP[target]))
            if l_b64: st.markdown(f'<div style="position: absolute; top: -10px; right: 20px; z-index: 1000;"><img src="data:image/png;base64,{l_b64}" style="height:65px;"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {target} 상세 실적 ({target_month}월)")
        mk = target.replace(' ', '').upper()

        # 물동량 테이블 (음영 보존)
        v_sub = df_v[df_v['match_name'] == mk][['구분'] + date_cols].copy()
        for c in date_cols: v_sub[c] = v_sub[c].apply(clean_value_to_float)
        vg = v_sub.groupby('구분', sort=False).sum().reset_index()
        vg.insert(1, '월 합계', vg[date_cols].sum(axis=1))
        vf = pd.concat([vg, pd.DataFrame([['일자별 합계', vg['월 합계'].sum()] + vg[date_cols].sum().tolist()], columns=vg.columns)], ignore_index=True)
        
        st.markdown("#### 1. 일자별 물동량")
        st.dataframe(vf.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(vf)-1 else '' for _ in x], axis=1)
                     .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 임시직 테이블 (음영 보존)
        st.markdown("---")
        st.markdown("#### 2. 일자별 임시직 투입")
        if not df_t.empty:
            tsub = df_t[df_t['match_name'] == mk].copy()
            trows = []
            for itm in ["남", "여", "지게차"]:
                rd = tsub[tsub['구분'] == itm]
                vals = [clean_value_to_float(rd[c].values[0]) if not rd.empty and c in rd.columns else 0.0 for c in date_cols]
                trows.append([itm] + vals)
            tdf = pd.DataFrame(trows, columns=['구분'] + date_cols)
            tdf.insert(1, '월 합계', tdf[date_cols].sum(axis=1))
            tf = pd.concat([tdf, pd.DataFrame([['일자별 합계', tdf['월 합계'].sum()] + tdf[date_cols].sum().tolist()], columns=tdf.columns)], ignore_index=True)
            
            st.dataframe(tf.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(tf)-1 else '' for _ in x], axis=1)
                         .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
