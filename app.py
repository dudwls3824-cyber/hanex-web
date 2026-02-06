import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

LOGO_DIR = "LOGO"
C_IMG = os.path.join(LOGO_DIR, "센터조감도.png")
H_LOG = os.path.join(LOGO_DIR, "한익스_LOGO.png")
L_MAP = {
    "DKSH L&L":"DKSH L&L_LOGO.png","대호 F&B":"대호 F&B_LOGO.png","덴비코리아":"덴비_LOGO.png",
    "막시무스코리아":"막시무스코리아.png","매그니프":"매그니프_LOGO.png","멘소래담":"멘소래담_LOGO.png",
    "머거본":"머거본_LOGO.png","바이오포트코리아":"바이오포트코리아_LOGO.png","시세이도":"시세이도_LOGO.png",
    "유니레버":"유니레버_LOGO.png","커머스파크":"커머스파크_LOGO.png","펄세스":"펄세스_LOGO.png",
    "PRODENTI":"프로덴티_LOGO.png","한국프리오":"한국프리오_LOGO.png","헨켈홈케어":"헨켈홈케어_LOGO.png",
    "네이처리퍼블릭":"네이처리퍼블릭_LOGO.png"
}

def get_b64(p):
    if os.path.exists(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def clean_num(x):
    if pd.isna(x) or str(x).strip() in ["", "-", "None", "nan"]: return 0.0
    try:
        s = str(x).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

@st.cache_data(ttl=1)
def fetch_data(sheet_name):
    """영진님의 월별 시트 호출 로직 (01월, 02월...)"""
    try:
        gsid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        # 월 선택 시 시트명에 '월'을 붙여서 호출
        target = f"{sheet_name}월" if sheet_name.isdigit() else sheet_name
        url = f"https://docs.google.com/spreadsheets/d/{gsid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(target)}"
        df_raw = pd.read_csv(url, header=None, dtype=str)
        h_idx = 0
        for i, row in df_raw.iterrows():
            if '화주사' in row.values: h_idx = i; break
        df = df_raw.iloc[h_idx+1:].copy()
        df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(df_raw.iloc[h_idx])]
        df = df.dropna(subset=['화주사', '구분'])
        df['match_name'] = df['화주사'].astype(str).str.replace(r'\s+', '', regex=True).str.upper()
        return df
    except: return pd.DataFrame()

# CSS 스타일 (배경, 투명 버튼, 슬라이더 로직 전체 보존)
bg_b64 = get_b64(C_IMG)
st.markdown(f"""
<style>
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), url('data:image/png;base64,{bg_b64}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .logo-container {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important; color: transparent !important; z-index: 100 !important;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin-bottom: 30px; overflow: hidden; position: relative; border-radius: 12px; display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    .slide-track {{ animation: scroll 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slide img {{ max-height: 70px; object-fit: contain; }}
    .top-right-logo {{ position: absolute; top: -10px; right: 20px; z-index: 1000; }}
</style>
""", unsafe_allow_html=True)

# --- 사이드바 및 데이터 로드 ---
with st.sidebar:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if st.button("H"): st.session_state.view = 'home'; st.rerun()
    if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("---")
    
    mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
    df_vol = fetch_data(mon)
    df_temp = fetch_data('임시직')

    if not df_vol.empty:
        comps = list(dict.fromkeys(df_vol['화주사'].tolist()))
        if 'view' not in st.session_state: st.session_state.view = 'home'
        if 'sel_comp' not in st.session_state: st.session_state.sel_comp = comps[0]
        curr_idx = comps.index(st.session_state.sel_comp) if st.session_state.sel_comp in comps else 0
        selected = st.radio("📍 화주사 목록", comps, index=curr_idx if st.session_state.view == 'detail' else None)
        if selected:
            st.session_state.view = 'detail'; st.session_state.sel_comp = selected
        
        # 날짜 열 추출 (01~31)
        date_cols = [c for c in df_vol.columns if re.search(r'^\d{1,2}$', str(c).strip())]

# --- 메인 화면 로직 ---
if not df_vol.empty:
    if st.session_state.view == 'home':
        st.title(f"📊 남이천1센터 {mon}월 물동량 Dash Board")
        
        # [행 복구] 로고 슬라이더 HTML 로직
        slides_html = "".join([f'<div class="slide"><img src="data:image/png;base64,{get_b64(os.path.join(LOGO_DIR, f))}"></div>' for n, f in L_MAP.items() if get_b64(os.path.join(LOGO_DIR, f))])
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        res = []
        for c in comps:
            m_name = re.sub(r'\s+', '', c).upper()
            v_sum = df_vol[df_vol['match_name'] == m_name][date_cols].applymap(clean_num).sum().sum()
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                act_t_cols = [tc for tc in date_cols if tc in t_sub.columns]
                t_sum = t_sub[act_t_cols].applymap(clean_num).sum().sum() if act_t_cols else 0
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        sum_df = pd.DataFrame(res)
        # [행 복구] 대형 물동량 박스 로직
        st.markdown(f"""<div style="background-color: #002D56; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700;">
            <h3 style="color: white; margin: 0;">📦 {mon}월 센터 전체 물동량 계</h3>
            <h1 style="color: #FFD700; margin: 10px 0; font-size: 3.5rem;">{int(sum_df["물동량 합계"].sum()):,}</h1></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.5, 1])
        with c1: st.bar_chart(sum_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2: st.dataframe(sum_df.assign(**{col: sum_df[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-") for col in ["물동량 합계", "임시직 합계"]}), use_container_width=True, hide_index=True, height=500)

    else:
        # --- 상세 페이지 (행 절대 생략 금지) ---
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            b_logo = get_b64(os.path.join(LOGO_DIR, L_MAP[menu]))
            if b_logo: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b_logo}" style="height:60px;"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {menu} {mon}월 상세 현황")
        m_name = re.sub(r'\s+', '', menu).upper()

        # 1. 물동량 상세 (음영 및 날짜별 합계 전체 보존)
        v_sub = df_vol[df_vol['match_name'] == m_name][['구분'] + date_cols].copy()
        for col in date_cols: v_sub[col] = v_sub[col].apply(clean_num)
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g.insert(1, '월 합계', v_g[date_cols].sum(axis=1))
        v_total = ['일자별 합계', v_g['월 합계'].sum()] + v_g[date_cols].sum().tolist()
        v_final = pd.concat([v_g, pd.DataFrame([v_total], columns=v_g.columns)], ignore_index=True)
        
        st.markdown("#### 1. 일자별 물동량 현황")
        st.dataframe(v_final.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(v_final)-1 else '' for _ in x], axis=1)
                     .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 2. 임시직 상세 (남, 여, 지게차 행 개수 정확히 보존)
        st.markdown("---")
        st.markdown("#### 2. 일자별 임시직 투입 현황")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['match_name'] == m_name].copy()
            t_rows = []
            for item in ["남", "여", "지게차"]:
                rd = t_sub[t_sub['구분'] == item]
                vals = [clean_num(rd[c].values[0]) if not rd.empty and c in rd.columns else 0.0 for c in date_cols]
                t_rows.append([item] + vals)
            t_df = pd.DataFrame(t_rows, columns=['구분'] + date_cols)
            t_df.insert(1, '월 합계', t_df[date_cols].sum(axis=1))
            t_total = ['일자별 합계', t_df['월 합계'].sum()] + t_df[date_cols].sum().tolist()
            t_final = pd.concat([t_df, pd.DataFrame([t_total], columns=t_df.columns)], ignore_index=True)
            
            st.dataframe(t_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(t_final)-1 else '' for _ in x], axis=1)
                         .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
