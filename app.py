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
    
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin: auto; overflow: hidden; position: relative; width: 100%; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; }}
    .slide-track {{ animation: scroll 60s ease-in-out infinite alternate; display: flex; width: calc(150px * 15); }}
    .slide {{ height: 80px; width: 150px; display: flex; align-items: center; justify-content: center; padding: 10px; }}
    .slide img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
    
    .top-right-logo {{ position: absolute; top: -10px; right: 0px; height: 80px; width: 200px; display: flex; justify-content: flex-end; align-items: center; z-index: 100; }}
    .top-right-logo img {{ height: 60px; width: auto; object-fit: contain; }}
    
    [data-testid='stMetric'] {{ background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; }}
    h1, h2, h3, h4 {{ color: #002D56 !important; font-weight: 900 !important; }}
    .logo-container {{ position: relative; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .stButton>button {{ position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 999 !important; cursor: pointer !important; }}
    </style>
    """, unsafe_allow_html=True)

def render_logo_slider():
    slides_html = ""
    for name, file in L_MAP.items():
        path = os.path.join(L_DIR, file)
        b64 = get_b64(path)
        if b64: slides_html += f'<div class="slide"><img src="data:image/png;base64,{b64}" title="{name}"></div>'
    st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)

apply_theme()

@st.cache_data(ttl=10)
def load_csv_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        raw_df = pd.read_csv(url, nrows=5)
        h_idx = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values: h_idx = i + 1; break
        df = pd.read_csv(url, header=h_idx)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['화주사', '구분'])
        return df[df['구분'].astype(str).str.lower() != 'none']
    except: return pd.DataFrame()

def to_n(x):
    try:
        if pd.isna(x) or str(x).lower() == "none": return 0
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["-", "", "nan", "0", "0.0"] else 0
    except: return 0

df_vol = load_csv_data('구글 데이터')
df_temp = load_csv_data('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df_vol.columns if "2026-" in c]
    comps = list(dict.fromkeys(df_vol['화주사'].dropna().tolist()))
    
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
        render_logo_slider()
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
            sdf_fmt = sdf.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_fmt[col] = sdf_fmt[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_fmt, use_container_width=True, hide_index=True, height=450)

    else:
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            logo_path = os.path.join(L_DIR, L_MAP[menu])
            b64_logo = get_b64(logo_path)
            if b64_logo: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_logo}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"## {menu} 상세 현황")

        def format_val(x):
            try:
                num = float(str(x).replace(',', ''))
                return f"{int(num):,}" if num > 0 else "-"
            except: return str(x)

        # 1. 물동량 현황 (일자별 합계 추가)
        st.markdown("#### 1. 물동량 현황")
        v_df = df_vol[df_vol['화주사'] == menu][['구분'] + t_cols].copy()
        for c in t_cols: v_df[c] = v_df[c].apply(to_n)
        v_g = v_df.groupby('구분', sort=False).sum().reset_index()
        v_g['월 합계'] = v_g[t_cols].sum(axis=1)
        
        # 물동량 일자별 합계 행 계산
        v_day_sum = v_g[['월 합계'] + t_cols].sum()
        v_sum_row = pd.DataFrame([['일자별 합계'] + v_day_sum.tolist()], columns=['구분', '월 합계'] + t_cols)
        v_final = pd.concat([v_g, v_sum_row], ignore_index=True).rename(columns={c: c.split("-")[-1] for c in t_cols})
        
        st.dataframe(v_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(format_val), use_container_width=True, hide_index=True)

        # 2. 임시직 현황
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_df = df_temp[df_temp['화주사'] == menu][['구분'] + t_cols].copy()
            for c in t_cols: t_df[c] = t_df[c].apply(to_n)
            t_g = t_df.groupby('구분', sort=False).sum().reset_index()
            temp_items = ["남", "여", "지게차"]
            for item in temp_items:
                if item not in t_g['구분'].values:
                    t_g = pd.concat([t_g, pd.DataFrame([{'구분':item, **{c:0 for c in t_cols}}])], ignore_index=True)
            t_g = t_g[t_g['구분'].isin(temp_items)].copy()
            t_g['구분'] = pd.Categorical(t_g['구분'], categories=temp_items, ordered=True)
            t_g = t_g.sort_values('구분')
            t_g['월 합계'] = t_g[t_cols].sum(axis=1)
            
            day_sum = t_g[['월 합계'] + t_cols].sum()
            sum_row = pd.DataFrame([['일자별 합계'] + day_sum.tolist()], columns=['구분', '월 합계'] + t_cols)
            t_final = pd.concat([t_g[['구분', '월 합계'] + t_cols], sum_row], ignore_index=True).rename(columns={c: c.split("-")[-1] for c in t_cols})
            
            st.dataframe(t_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(format_val), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
