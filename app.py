import streamlit as st
import pandas as pd
import urllib.parse, os, base64

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 이미지 및 로고 설정
L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")
L_MAP = {
    "DKSH L&L":"DKSH L&L_LOGO.png","대호 F&B":"대호 F&B_LOGO.png","덴비코리아":"덴비_LOGO.png",
    "막시무스코리아":"막시무스_LOGO.png","매그니프":"매그니프_LOGO.png","멘소래담":"멘소래담_LOGO.png",
    "머거본":"머거본_LOGO.png","바이오포트코리아":"바이오포트코리아_LOGO.png","시세이도":"시세이도_LOGO.png",
    "유니레버":"유니레버_LOGO.png","커머스파크":"커머스파크_LOGO.png","펄세스":"펄세스_LOGO.png",
    "PRODENTI":"프로덴티_LOGO.png","한국프리오":"한국프리오_LOGO.png","헨켈홈케어":"헨켈홈케어_LOGO.png"
}

def get_b64(p):
    if os.path.exists(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def apply_theme():
    b64_bg = get_b64(C_IMG)
    st.markdown(f"""
    <style>
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{b64_bg}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid='stSidebar'] {{ background-color: #FFFFFF !important; border-top: 25px solid #E30613 !important; border-bottom: 35px solid #002D56 !important; }}
    [data-testid='stMetric'] {{ background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; }}
    h1, h2, h3, h4 {{ color: #002D56 !important; font-weight: 900 !important; }}
    .logo-container {{ position: relative; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .stButton>button {{ position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 999 !important; cursor: pointer !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# --- 데이터 로드 ---
@st.cache_data(ttl=10)
def load_csv_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        raw_df = pd.read_csv(url, nrows=5)
        header_idx = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values: header_idx = i + 1; break
        df = pd.read_csv(url, header=header_idx)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['화주사', '구분'])
        # 'None' 텍스트 행 완전 제거
        df = df[df['구분'].astype(str).str.lower() != 'none']
        return df
    except: return pd.DataFrame()

def to_n(x):
    try:
        if pd.isna(x) or str(x).lower() == "none" or str(x).strip() == "": return 0
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["-", "nan", "NaN", "0", "0.0"] else 0
    except: return 0

df_vol = load_csv_data('구글 데이터')
df_temp = load_csv_data('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df_vol.columns if "2026-" in c]
    comps = sorted(list(set(df_vol['화주사'].dropna().tolist())))
    
    with st.sidebar:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if st.button("HOME", key="home_btn"): st.session_state.view = 'home'; st.rerun()
        if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        selected = st.radio("📍 화주사 목록", comps, index=None if st.session_state.view == 'home' else (comps.index(st.session_state.sel_comp) if 'sel_comp' in st.session_state else 0))
        if selected: st.session_state.view = 'detail'; st.session_state.sel_comp = selected
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        t_cols = [c for c in cols2026 if c.startswith(f"2026-{mon}")]

    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        res = []
        for c in comps:
            v_sum = df_vol[df_vol['화주사'] == c][t_cols].applymap(to_n).sum().sum()
            t_sum = df_temp[df_temp['화주사'] == c][t_cols].applymap(to_n).sum().sum() if not df_temp.empty else 0
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        sdf = pd.DataFrame(res)
        
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['물동량 합계'].sum()):,}")
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(f"#### 📈 화주사별 분석 ({mon}월)")
            st.bar_chart(sdf.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            # 숫자 포맷팅 및 열 너비 조정
            sdf_fmt = sdf.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_fmt[col] = sdf_fmt[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_fmt, use_container_width=True, hide_index=True, height=450)

    else:
        # --- 상세 페이지 ---
        menu = st.session_state.sel_comp
        st.markdown(f"## {menu} 상세 현황")

        def format_val(x):
            try:
                num = float(str(x).replace(',', ''))
                return f"{int(num):,}" if num > 0 else "-"
            except: return str(x)

        # 1. 물동량 표
        st.markdown("#### 1. 물동량 현황")
        v_detail = df_vol[df_vol['화주사'] == menu][['구분'] + t_cols].copy()
        for c in t_cols: v_detail[c] = v_detail[c].apply(to_n)
        v_grouped = v_detail.groupby('구분', sort=False).sum().reset_index()
        v_grouped['월 합계'] = v_grouped[t_cols].sum(axis=1)
        v_disp = v_grouped[['구분', '월 합계'] + t_cols].rename(columns={c: c.split("-")[-1] for c in t_cols})
        st.dataframe(v_disp.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(format_val), use_container_width=True, hide_index=True)

        # 2. 임시직 표 (None 제거 버전)
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_detail = df_temp[df_temp['화주사'] == menu][['구분'] + t_cols].copy()
            for c in t_cols: t_detail[c] = t_detail[c].apply(to_n)
            t_grouped = t_detail.groupby('구분', sort=False).sum().reset_index()
            
            # 항목 강제 고정 및 'None' 필터링
            temp_items = ["남", "여", "지게차"]
            for item in temp_items:
                if item not in t_grouped['구분'].values:
                    t_grouped = pd.concat([t_grouped, pd.DataFrame([{'구분':item, **{c:0 for c in t_cols}}])], ignore_index=True)
            
            t_grouped = t_grouped[t_grouped['구분'].isin(temp_items)].copy()
            t_grouped['구분'] = pd.Categorical(t_grouped['구분'], categories=temp_items, ordered=True)
            t_grouped = t_grouped.sort_values('구분')
            t_grouped['월 합계'] = t_grouped[t_cols].sum(axis=1)
            
            # 일자별 합계 추가
            day_sum = t_grouped[['월 합계'] + t_cols].sum()
            sum_row = pd.DataFrame([['일자별 합계'] + day_sum.tolist()], columns=['구분', '월 합계'] + t_cols)
            t_final = pd.concat([t_grouped[['구분', '월 합계'] + t_cols], sum_row], ignore_index=True).rename(columns={c: c.split("-")[-1] for c in t_cols})
            
            st.dataframe(t_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(format_val), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
