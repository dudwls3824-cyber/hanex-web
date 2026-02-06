import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", page_icon="📦", layout="wide")

LOGO_DIR = "LOGO"
C_IMG = os.path.join(LOGO_DIR, "센터조감도.png")
H_LOG = os.path.join(LOGO_DIR, "한익스_LOGO.png")
L_MAP = {
    "DKSH L&L":"DKSH L&L_LOGO.png", "대호 F&B":"대호 F&B_LOGO.png", "덴비코리아":"덴비_LOGO.png",
    "막시무스코리아":"막시무스코리아.png", "매그니프":"매그니프_LOGO.png", "멘소래담":"멘소래담_LOGO.png",
    "머거본":"머거본_LOGO.png", "바이오포트코리아":"바이오포트코리아_LOGO.png", "시세이도":"시세이도_LOGO.png",
    "유니레버":"유니레버_LOGO.png", "커머스파크":"커머스파크_LOGO.png", "펄세스":"펄세스_LOGO.png",
    "PRODENTI":"프로덴티_LOGO.png", "한국프리오":"한국프리오_LOGO.png", "헨켈홈케어":"헨켈홈케어_LOGO.png",
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
        df = df[df['화주사'].fillna('').str.strip() != ''].copy()
        df['match_name'] = df['화주사'].astype(str).str.replace(r'\s+', '', regex=True).str.upper()
        return df
    except: return pd.DataFrame()

# CSS 스타일링 (영진님 원본 유지)
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

with st.sidebar:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if st.button("HOME_CLICK"): st.session_state.view = 'home'; st.rerun()
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
        if selected: st.session_state.view = 'detail'; st.session_state.sel_comp = selected
        
        # [수정] 타 월 데이터 필터링: 선택한 월(mon)의 날짜만 열로 추출
        # 열 이름이 '2026-01-01' 형식이든 '1' 형식이든 선택한 월과 일치하는 것만 필터링
        date_cols = [c for c in df_vol.columns if re.search(rf'[-]{mon}[-]|[\s]{mon}[\s]|^{mon}$|^\d{{1,2}}$', str(c)) or (len(str(c)) <= 2 and str(c).isdigit())]
        # 만약 시트 구조상 위 정규식이 복잡하다면, 단순하게 '화주사', '구분' 등 제외한 뒤 mon 정보가 포함된 열만 남김
        date_cols = [c for c in date_cols if c not in ['화주사', '구분', 'match_name', '월 합계', '월합계']]

if not df_vol.empty:
    if st.session_state.view == 'home':
        st.title(f"📊 남이천1센터 {mon}월 대시보드")
        slides_html = "".join([f'<div class="slide"><img src="data:image/png;base64,{get_b64(os.path.join(LOGO_DIR, f))}"></div>' for n, f in L_MAP.items() if get_b64(os.path.join(LOGO_DIR, f))])
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        res = []
        for c in comps:
            m_name = re.sub(r'\s+', '', c).upper()
            v_sum = df_vol[df_vol['match_name'] == m_name][date_cols].applymap(clean_num).sum().sum()
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                # 임시직도 해당 월 날짜만 매칭
                t_cols = [tc for tc in date_cols if tc in t_sub.columns]
                t_sum = t_sub[t_cols].applymap(clean_num).sum().sum() if t_cols else 0
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        sum_df = pd.DataFrame(res)
        
        st.markdown(f"""<div style="background-color: #002D56; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700;">
            <h3 style="color: white; margin: 0;">📦 {mon}월 센터 전체 물동량 계</h3>
            <h1 style="color: #FFD700; margin: 10px 0; font-size: 3.5rem;">{int(sum_df["물동량 합계"].sum()):,}</h1></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.5, 1])
        with c1: st.bar_chart(sum_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2: st.dataframe(sum_df.assign(**{col: sum_df[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-") for col in ["물동량 합계", "임시직 합계"]}), use_container_width=True, hide_index=True, height=500)

    else:
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            b_logo = get_b64(os.path.join(LOGO_DIR, L_MAP[menu]))
            if b_logo: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b_logo}" style="height:60px;"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {menu} {mon}월 상세 현황")
        m_name = re.sub(r'\s+', '', menu).upper()

        # 1. 물동량 상세 (선택한 월의 날짜 열만 표시)
        v_final = df_vol[df_vol['match_name'] == m_name][['구분'] + date_cols].copy()
        for col in date_cols: v_final[col] = v_final[col].apply(clean_num)
        v_final.insert(1, '월 합계', v_final[date_cols].sum(axis=1))
        
        v_total_row = ['일자별 합계', v_final['월 합계'].sum()] + v_final[date_cols].sum().tolist()
        v_display = pd.concat([v_final, pd.DataFrame([v_total_row], columns=v_final.columns)], ignore_index=True)
        
        st.dataframe(v_display.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(v_display)-1 else '' for _ in x], axis=1)
                     .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 2. 임시직 상세 (원본 행 전체 복구)
        st.markdown("---")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['match_name'] == m_name]
            t_cols = [tc for tc in date_cols if tc in t_sub.columns]
            # [복구] '구분' 열을 포함하여 임시직 행 전체를 누락 없이 출력
            t_final = t_sub[['구분'] + t_cols].copy()
            for col in t_cols: t_final[col] = t_final[col].apply(clean_num)
            
            t_final.insert(1, '월 합계', t_final[t_cols].sum(axis=1))
            t_total_row = ['일자별 합계', t_final['월 합계'].sum()] + t_final[t_cols].sum().tolist()
            t_display = pd.concat([t_final, pd.DataFrame([t_total_row], columns=t_final.columns)], ignore_index=True)
            
            st.dataframe(t_display.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(t_display)-1 else '' for _ in x], axis=1)
                         .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
