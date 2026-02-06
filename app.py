import streamlit as st
import pandas as pd
import urllib.parse, os, base64

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 로고 및 이미지 설정
L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")
L_MAP = {
    "DKSH L&L":"DKSH L&L_LOGO.png","대호 F&B":"대호 F&B_LOGO.png","덴비코리아":"덴비_LOGO.png",
    "막시무스코리아":"막시무스_LOGO.png","매그니프":"매그니프_LOGO.png","멘소래담":"멘소래담_LOGO.png",
    "머거본":"머거본_LOGO.png","바이오포트코리아":"바이오포트코리아_LOGO.png","시세이도":"시세이도_LOGO.png",
    "유니레버":"유니레버_LOGO.png","커머스파크":"커머스파크_LOGO.png","펄세스":"펄세스_LOGO.png",
    "PRODENTI":"프로덴티_LOGO.png","한국프리오":"한국프리오_LOGO.png","헨켈홈케어":"헨켈홈케어_LOGO.png",
    "네이처리퍼블릭":"네이처리퍼블릭_LOGO.png"
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
    .slide-track {{ animation: scroll 25s ease-in-out infinite alternate; display: flex; width: calc(150px * 16); }}
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

apply_theme()

@st.cache_data(ttl=5)
def load_sheet(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        raw = pd.read_csv(url, header=None)
        # '화주사' 글자가 있는 행 찾기
        h_row = -1
        for i, row in raw.iterrows():
            if '화주사' in row.astype(str).values:
                h_row = i
                break
        if h_row == -1: return pd.DataFrame()
        
        # 찾은 행을 헤더로 설정
        df = pd.read_csv(url, header=h_row)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['화주사', '구분'])
        df['화주사'] = df['화주사'].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def to_n(x):
    try:
        if pd.isna(x): return 0
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["-", "", "nan", "None", "0", "0.0"] else 0
    except: return 0

df_vol = load_sheet('구글 데이터')
df_temp = load_sheet('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df_vol.columns if "2026-" in c]
    comps = sorted(list(set(df_vol['화주사'].unique())))
    
    with st.sidebar:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if st.button("HOME", key="home_btn"): st.session_state.view = 'home'; st.rerun()
        if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        selected = st.radio("📍 화주사 목록", comps, index=None if st.session_state.view == 'home' else (comps.index(st.session_state.sel_comp) if 'sel_comp' in st.session_state else 0))
        if selected: st.session_state.view = 'detail'; st.session_state.sel_comp = selected
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)], index=0)
        t_cols = [c for c in cols2026 if c.startswith(f"2026-{mon}")]

    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        # 로고 슬라이더 (속도 25s 반영)
        slides_html = "".join([f'<div class="slide"><img src="data:image/png;base64,{get_b64(os.path.join(L_DIR, f))}"></div>' for n, f in L_MAP.items() if get_b64(os.path.join(L_DIR, f))])
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        # 홈 화면 요약 데이터 계산
        res = []
        for c in comps:
            v_sum = df_vol[df_vol['화주사'] == c][t_cols].applymap(to_n).sum().sum()
            t_sum = 0
            if not df_temp.empty:
                # 공백 무시하고 매칭 (매그니프 등 대응)
                t_match = df_temp[df_temp['화주사'].str.replace(' ','') == c.replace(' ','')]
                t_cols_act = [col for col in t_cols if col in df_temp.columns]
                t_sum = t_match[t_cols_act].applymap(to_n).sum().sum()
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        sdf = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['물동량 합계'].sum()):,}")
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(f"#### 📈 화주사별 분석 ({mon}월)")
            st.bar_chart(sdf.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            sdf_disp = sdf.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_disp[col] = sdf_disp[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_disp, use_container_width=True, hide_index=True, height=450)

    else:
        # 상세 페이지
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            b64_logo = get_b64(os.path.join(L_DIR, L_MAP[menu]))
            if b64_logo: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_logo}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"## {menu} 상세 현황")

        def fmt(x):
            try:
                n = float(str(x).replace(',', ''))
                return f"{int(n):,}" if n > 0 else "-"
            except: return str(x)

        # 1. 물동량 (월 합계 2번째 열 고정)
        v_sub = df_vol[df_vol['화주사'] == menu][['구분'] + t_cols].copy()
        for c in t_cols: v_sub[c] = v_sub[c].apply(to_n)
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g['월 합계'] = v_g[t_cols].sum(axis=1)
        v_sum_row = pd.DataFrame([['일자별 합계'] + v_g[['월 합계']+t_cols].sum().tolist()], columns=['구분', '월 합계']+t_cols)
        v_final = pd.concat([v_g, v_sum_row], ignore_index=True)
        
        st.markdown("#### 1. 물동량 현황")
        st.dataframe(v_final[['구분', '월 합계'] + t_cols].rename(columns={c: c.split("-")[-1] for c in t_cols}).style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(fmt), use_container_width=True, hide_index=True)

        # 2. 임시직 (매칭 강화 및 월 합계 2번째 열 고정)
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['화주사'].str.replace(' ','') == menu.replace(' ','')].copy()
            t_cols_act = [col for col in t_cols if col in df_temp.columns]
            
            if not t_sub.empty:
                for c in t_cols_act: t_sub[c] = t_sub[c].apply(to_n)
                t_g = t_sub.groupby('구분', sort=False).sum().reset_index()
                # 필수 항목 보장
                for itm in ["남", "여", "지게차"]:
                    if itm not in t_g['구분'].values:
                        t_g = pd.concat([t_g, pd.DataFrame([{'구분':itm, **{c:0 for c in t_cols_act}}])], ignore_index=True)
                t_g = t_g[t_g['구분'].isin(["남", "여", "지게차"])].copy()
                t_g['구분'] = pd.Categorical(t_g['구분'], categories=["남", "여", "지게차"], ordered=True)
                t_g = t_g.sort_values('구분')
                t_g['월 합계'] = t_g[t_cols_act].sum(axis=1)
                
                t_sum_row = pd.DataFrame([['일자별 합계'] + t_g[['월 합계']+t_cols_act].sum().tolist()], columns=['구분', '월 합계']+t_cols_actual if 't_cols_actual' in locals() else ['구분', '월 합계']+t_cols_act)
                t_final = pd.concat([t_g, t_sum_row], ignore_index=True)
                for c in t_cols:
                    if c not in t_final.columns: t_final[c] = 0
                
                st.dataframe(t_final[['구분', '월 합계'] + t_cols].rename(columns={c: c.split("-")[-1] for c in t_cols}).style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0).format(fmt), use_container_width=True, hide_index=True)
            else:
                st.info(f"'{menu}' 임시직 데이터가 없습니다.")

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
