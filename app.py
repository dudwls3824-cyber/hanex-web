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
    [data-testid="stSidebarCollapseButton"] {{
        background-color: #002D56 !important; color: white !important; border-radius: 5px !important;
        top: 10px !important; right: -20px !important; opacity: 1 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin: auto; overflow: hidden; position: relative; width: 100%; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; }}
    .slide-track {{ animation: scroll 60s ease-in-out infinite alternate; display: flex; width: calc(150px * 15); }}
    .slide {{ height: 80px; width: 150px; display: flex; align-items: center; justify-content: center; padding: 10px; }}
    .slide img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
    [data-testid='stMetric'] {{ background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; }}
    h1, h2, h3 {{ color: #002D56 !important; font-weight: 900 !important; }}
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

URL = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('구글 데이터')}"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = df.columns.str.strip()
        return df.dropna(subset=['화주사'])
    except: return None

def to_n(x):
    try:
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["", "-", "None", "nan", "NaN", "0"] else 0
    except: return 0

df = load_data()

if df is not None:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df.columns if "2026-" in c]
    comps = list(dict.fromkeys(df['화주사'].dropna().tolist()))
    
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
        st.title("📊 남이천1센터 물동량 Dash Board")
        render_logo_slider()
        res = []
        for c in comps:
            cdf = df[df['화주사'] == c]
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
            st.dataframe(sdf.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x), use_container_width=True, hide_index=True, height=380)

    else:
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            p = os.path.join(L_DIR, L_MAP[menu])
            if os.path.exists(p): st.image(p, width=180)
        st.markdown(f"## {menu} 상세 현황")
        cdf = df[df['화주사'] == menu]
        if not cdf.empty:
            # 🔥 [해결] 구분값 순서 유지를 위해 원본 구분값 리스트 미리 확보
            orig_order = list(dict.fromkeys(cdf['구분'].dropna().tolist()))
            
            df_detail = cdf[cdf['구분'].notna()][['구분'] + t_cols].copy()
            for c in t_cols: df_detail[c] = df_detail[c].apply(to_n)
            
            # 그룹화 후 원본 순서대로 재정렬
            df_grouped = df_detail.groupby('구분', sort=False).sum().reset_index()
            df_grouped['구분'] = pd.Categorical(df_grouped['구분'], categories=orig_order, ordered=True)
            df_grouped = df_grouped.sort_values('구분')
            
            # 월 합계 계산 및 위치 조정
            df_grouped['월 합계'] = df_grouped[t_cols].sum(axis=1)
            dt_display = df_grouped[['구분', '월 합계'] + t_cols].copy()
            
            # 그래프 출력
            df_chart = df_grouped.set_index('구분')[t_cols].transpose()
            df_chart.index = df_chart.index.map(lambda x: x.split("-")[-1])
            fig = go.Figure()
            for column in df_chart.columns:
                fig.add_trace(go.Bar(name=str(column), x=df_chart.index, y=df_chart[column]))
            fig.add_trace(go.Scatter(name='일일 합계', x=df_chart.index, y=df_chart.sum(axis=1), mode='lines+markers', line=dict(color='#E30613', width=3)))
            fig.update_layout(barmode='stack', hovermode="x unified", legend=dict(orientation="h", y=1.1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # 🔥 [해결] 숫자 0을 '-'로 변환하여 표 출력 (음영 유지)
            new_cols = {c: c.split("-")[-1] for c in t_cols}
            dt_final = dt_display.rename(columns=new_cols)
            
            def format_val(x):
                if isinstance(x, (int, float)):
                    return f"{int(x):,}" if x > 0 else "-"
                return x

            # 스타일 적용 (월 합계 열 음영)
            def style_row(row):
                return ['' if col != '월 합계' else 'background-color: #F0F2F6; font-weight: bold;' for col in dt_final.columns]

            st.dataframe(dt_final.style.apply(style_row, axis=1).format(format_val), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
