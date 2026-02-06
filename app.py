import streamlit as st
import pandas as pd
import urllib.parse, os, base64
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 경로 및 이미지 설정
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
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def apply_theme():
    b64_bg = get_b64(C_IMG)
    bg_css = f"""
    <style>
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                          url('data:image/png;base64,{b64_bg}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid='stSidebar'] {{ background-color: #FFFFFF !important; border-top: 25px solid #E30613 !important; border-bottom: 35px solid #002D56 !important; }}
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin: auto; overflow: hidden; position: relative; width: 100%; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; }}
    .slide-track {{ animation: scroll 60s ease-in-out infinite alternate; display: flex; width: calc(150px * 15); }}
    .slide {{ height: 80px; width: 150px; display: flex; align-items: center; justify-content: center; padding: 10px; }}
    .slide img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
    [data-testid='stMetric'] {{ background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; }}
    h1, h2, h3, h4 {{ color: #002D56 !important; font-weight: 900 !important; }}
    .logo-container {{ position: relative; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .stButton>button {{ position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 999 !important; cursor: pointer !important; }}
    </style>
    """
    st.markdown(bg_css, unsafe_allow_html=True)

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
        header_idx = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values:
                header_idx = i + 1
                break
        df = pd.read_csv(url, header=header_idx)
        df.columns = df.columns.str.strip()
        return df.fillna(0) # None 방지: 빈 칸은 0으로 채움
    except:
        return pd.DataFrame()

def to_n(x):
    try:
        if pd.isna(x) or x == "None" or x == "": return 0
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["-", "nan", "NaN", "0", "0.0"] else 0
    except: return 0

df_vol = load_csv_data('구글 데이터')
df_temp = load_csv_data('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df_vol.columns if "2026-" in c]
    comps = list(dict.fromkeys(df_vol['화주사'].dropna().tolist()))
    if 0 in comps: comps.remove(0) # 데이터 청소
    
    with st.sidebar:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if st.button("HOME", key="home_btn"):
            st.session_state.view = 'home'
            st.rerun()
        if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        selected = st.radio("📍 화주사 목록", comps, index=None if st.session_state.view == 'home' else (comps.index(st.session_state.sel_comp) if 'sel_comp' in st.session_state else 0))
        if selected:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = selected
            
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        t_cols = [c for c in cols2026 if c.startswith(f"2026-{mon}")]

    if st.session_state.view == 'home':
        # --- [복구] 홈 화면 내용 ---
        st.title("📊 남이천1센터 물동량 Dash Board")
        render_logo_slider()
        res = []
        for c in comps:
            cdf = df_vol[df_vol['화주사'] == c]
            v_sum = cdf[t_cols].applymap(to_n).sum().sum()
            res.append({"화주사": c, "월 물동량 합계": v_sum})
        sdf = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['월 물동량 합계'].sum()):,}")
        
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.markdown(f"#### 📈 화주사별 분석 ({mon}월)")
            st.bar_chart(sdf.set_index('화주사'), color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            st.dataframe(sdf.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x), use_container_width=True, hide_index=True, height=400)

    else:
        # --- 상세 페이지 ---
        menu = st.session_state.sel_comp
        if menu in L_MAP and os.path.exists(os.path.join(L_DIR, L_MAP[menu])):
            st.image(os.path.join(L_DIR, L_MAP[menu]), width=180)
        st.markdown(f"## {menu} 상세 현황")

        def style_sum_column(df_data):
            styles = pd.DataFrame('', index=df_data.index, columns=df_data.columns)
            if '월 합계' in df_data.columns:
                styles['월 합계'] = 'background-color: #F0F2F6; font-weight: bold;'
            return styles

        def format_val(x):
            try:
                num = float(str(x).replace(',', ''))
                return f"{int(num):,}" if num > 0 else "-"
            except: return str(x)

        # --- 1. 물동량 현황 ---
        st.markdown("#### 1. 물동량 현황")
        v_df = df_vol[df_vol['화주사'] == menu]
        if not v_df.empty:
            v_orig_order = list(dict.fromkeys(v_df['구분'].dropna().tolist()))
            v_detail = v_df[v_df['구분'] != 0][['구분'] + t_cols].copy()
            for c in t_cols: v_detail[c] = v_detail[c].apply(to_n)
            
            v_grouped = v_detail.groupby('구분', sort=False).sum().reset_index()
            v_grouped['월 합계'] = v_grouped[t_cols].sum(axis=1)
            
            v_display = v_grouped[['구분', '월 합계'] + t_cols].copy()
            new_date_cols = {c: c.split("-")[-1] for c in t_cols}
            v_display = v_display.rename(columns=new_date_cols)
            
            # 음영 적용 표 출력
            st.dataframe(v_display.style.apply(style_sum_column, axis=None).format(format_val), use_container_width=True, hide_index=True)

        # --- 2. 임시직 투입 현황 ---
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_df = df_temp[df_temp['화주사'] == menu]
            temp_items = ["남", "여", "지게차"]
            
            t_detail = t_df[t_df['구분'] != 0][['구분'] + t_cols].copy()
            for c in t_cols: t_detail[c] = t_detail[c].apply(to_n)
            
            t_grouped = t_detail.groupby('구분', sort=False).sum().reset_index()
            # 항목 강제 고정
            for item in temp_items:
                if item not in t_grouped['구분'].values:
                    t_grouped = pd.concat([t_grouped, pd.DataFrame([{'구분':item, **{c:0 for c in t_cols}}])], ignore_index=True)
            
            t_grouped['구분'] = pd.Categorical(t_grouped['구분'], categories=temp_items, ordered=True)
            t_grouped = t_grouped.sort_values('구분')
            t_grouped['월 합계'] = t_grouped[t_cols].sum(axis=1)
            
            # 일자별 합계 추가
            day_sum = t_grouped[['월 합계'] + t_cols].sum()
            sum_row = pd.DataFrame([['일자별 합계'] + day_sum.tolist()], columns=['구분', '월 합계'] + t_cols)
            t_final = pd.concat([t_grouped[['구분', '월 합계'] + t_cols], sum_row], ignore_index=True)
            t_final = t_final.rename(columns=new_date_cols)
            
            # 음영 적용 표 출력
            st.dataframe(t_final.style.apply(style_sum_column, axis=None).format(format_val), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
