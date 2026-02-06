import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# 1. 페이지 설정
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
    try:
        gsid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        target = f"{sheet_name}월" if sheet_name.isdigit() else sheet_name
        url = f"https://docs.google.com/spreadsheets/d/{gsid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(target)}"
        df_raw = pd.read_csv(url, header=None, dtype=str)
        
        h_idx = 0
        for i, row in df_raw.iterrows():
            if '화주사' in row.values: h_idx = i; break
        
        df = df_raw.iloc[h_idx+1:].copy()
        df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(df_raw.iloc[h_idx])]
        # [핵심] 화주사 이름이 적힌 행은 무조건 다 가져옴 (중복 허용)
        df = df[df['화주사'].fillna('').str.strip() != ''].copy()
        df['match_name'] = df['화주사'].astype(str).str.replace(r'\s+', '', regex=True).str.upper()
        return df
    except: return pd.DataFrame()

# 배경 및 스타일
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
    .top-right-logo {{ position: absolute; top: -10px; right: 20px; z-index: 1000; }}
</style>
""", unsafe_allow_html=True)

# --- 사이드바 ---
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
        # 중복 제거 없이 화주사 리스트 생성
        comps = list(dict.fromkeys(df_vol['화주사'].tolist()))
        if 'view' not in st.session_state: st.session_state.view = 'home'
        if 'sel_comp' not in st.session_state: st.session_state.sel_comp = comps[0]
        
        curr_idx = comps.index(st.session_state.sel_comp) if st.session_state.sel_comp in comps else 0
        selected = st.radio("📍 화주사 목록", comps, index=curr_idx if st.session_state.view == 'detail' else None)
        if selected:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = selected
        
        date_cols = [c for c in df_vol.columns if re.search(r'^\d{1,2}$', str(c).strip())]

# --- 메인 로직 ---
if not df_vol.empty:
    if st.session_state.view == 'home':
        st.title(f"📊 {mon}월 대시보드")
        # 홈 요약 정보... (생략 없이 원본 유지)
        st.write("화주사별 요약 현황")
        res = []
        for c in comps:
            m_name = re.sub(r'\s+', '', c).upper()
            v_sum = df_vol[df_vol['match_name'] == m_name][date_cols].applymap(clean_num).sum().sum()
            res.append({"화주사": c, "물동량 합계": v_sum})
        st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True)

    else:
        # --- 상세 페이지: 시세이도/DKSH 등 모든 행 100% 노출 ---
        menu = st.session_state.sel_comp
        st.markdown(f"### 🏢 {menu} {mon}월 상세 현황")
        m_name = re.sub(r'\s+', '', menu).upper()

        # 1. 물동량 상세 (가공 없이 원본 행 그대로 필터링)
        v_final = df_vol[df_vol['match_name'] == m_name][['구분'] + date_cols].copy()
        for col in date_cols: v_final[col] = v_final[col].apply(clean_num)
        
        # 행별 합계
        v_final.insert(1, '월 합계', v_final[date_cols].sum(axis=1))
        
        # 전체 합계 행 추가
        v_total_row = ['일자별 합계', v_final['월 합계'].sum()] + v_final[date_cols].sum().tolist()
        v_display = pd.concat([v_final, pd.DataFrame([v_total_row], columns=v_final.columns)], ignore_index=True)
        
        st.dataframe(v_display.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(v_display)-1 else '' for _ in x], axis=1)
                     .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 2. 임시직 상세 (원본 행 그대로 노출)
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_final = df_temp[df_temp['match_name'] == m_name][['구분'] + date_cols].copy()
            for col in date_cols:
                if col in t_final.columns: t_final[col] = t_final[col].apply(clean_num)
                else: t_final[col] = 0.0
            
            t_final.insert(1, '월 합계', t_final[date_cols].sum(axis=1))
            t_total_row = ['일자별 합계', t_final['월 합계'].sum()] + t_final[date_cols].sum().tolist()
            t_display = pd.concat([t_final, pd.DataFrame([t_total_row], columns=t_final.columns)], ignore_index=True)
            
            st.dataframe(t_display.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(t_display)-1 else '' for _ in x], axis=1)
                         .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
