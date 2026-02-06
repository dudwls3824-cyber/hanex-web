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
    h1, h2, h3, h4 {{ color: #002D56 !important; font-weight: 900 !important; }}
    .logo-container {{ position: relative; width: 100%; height: 80px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .stButton>button {{ position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; color: transparent !important; z-index: 999 !important; cursor: pointer !important; }}
    </style>
    """
    st.markdown(bg_css, unsafe_allow_html=True)

apply_theme()

# --- 튼튼한 데이터 로드 함수 ---
@st.cache_data(ttl=10)
def load_csv_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        # 첫 5줄을 읽어서 '화주사'가 포함된 줄을 헤더로 찾음
        raw_df = pd.read_csv(url, nrows=5)
        header_idx = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values:
                header_idx = i + 1
                break
        
        df = pd.read_csv(url, header=header_idx)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

def to_n(x):
    try:
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["", "-", "None", "nan", "NaN", "0", "0.0"] else 0
    except: return 0

# 데이터 로드
df_vol = load_csv_data('구글 데이터')
df_temp = load_csv_data('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    cols2026 = [c for c in df_vol.columns if "2026-" in c]
    comps = list(dict.fromkeys(df_vol['화주사'].dropna().tolist()))
    
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
        # 홈 요약 로직 생략(기존과 동일)
    else:
        # --- 상세 페이지 ---
        menu = st.session_state.sel_comp
        if menu in L_MAP and os.path.exists(os.path.join(L_DIR, L_MAP[menu])):
            st.image(os.path.join(L_DIR, L_MAP[menu]), width=180)
        st.markdown(f"## {menu} 상세 현황")

        # 공통 포맷팅 함수 (0 -> '-')
        def format_with_dash(target_df, cols):
            for c in cols:
                target_df[c] = target_df[c].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            return target_df

        # --- 1. 물동량 현황 ---
        st.markdown("#### 1. 물동량 현황")
        v_df = df_vol[df_vol['화주사'] == menu]
        if not v_df.empty:
            v_orig_order = list(dict.fromkeys(v_df['구분'].dropna().tolist()))
            v_detail = v_df[v_df['구분'].notna()][['구분'] + t_cols].copy()
            for c in t_cols: v_detail[c] = v_detail[c].apply(to_n)
            
            v_grouped = v_detail.groupby('구분', sort=False).sum().reset_index()
            v_grouped['월 합계'] = v_grouped[t_cols].sum(axis=1)
            
            v_display = v_grouped[['구분', '월 합계'] + t_cols].copy()
            new_date_cols = {c: c.split("-")[-1] for c in t_cols}
            v_display = v_display.rename(columns=new_date_cols)
            
            # 스타일: 월 합계 열 음영
            st.dataframe(format_with_dash(v_display, ['월 합계'] + list(new_date_cols.values())), use_container_width=True, hide_index=True)

        # --- 2. 임시직 투입 현황 ---
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_df = df_temp[df_temp['화주사'] == menu]
            if not t_df.empty:
                temp_items = ["남", "여", "지게차"]
                t_detail = t_df[t_df['구분'].notna()][['구분'] + t_cols].copy()
                for c in t_cols: t_detail[c] = t_detail[c].apply(to_n)
                
                t_grouped = t_detail.groupby('구분', sort=False).sum().reset_index()
                # 항목 고정
                for item in temp_items:
                    if item not in t_grouped['구분'].values:
                        t_grouped = pd.concat([t_grouped, pd.DataFrame([{'구분':item, **{c:0 for c in t_cols}}])], ignore_index=True)
                
                t_grouped['구분'] = pd.Categorical(t_grouped['구분'], categories=temp_items, ordered=True)
                t_grouped = t_grouped.sort_values('구분')
                t_grouped['월 합계'] = t_grouped[t_cols].sum(axis=1)
                
                # 하단 일자별 합계 계산
                day_sum = t_grouped[ ['월 합계'] + t_cols ].sum()
                sum_row = pd.DataFrame([['일자별 합계'] + day_sum.tolist()], columns=['구분', '월 합계'] + t_cols)
                t_final = pd.concat([t_grouped[['구분', '월 합계'] + t_cols], sum_row], ignore_index=True)
                
                t_final = t_final.rename(columns=new_date_cols)
                
                # 마지막 행(일자별 합계) 강조 스타일은 라이브러리 제약상 텍스트로 대체하거나 간단히 출력
                st.dataframe(format_with_dash(t_final, ['월 합계'] + list(new_date_cols.values())), use_container_width=True, hide_index=True)
            else:
                st.info("해당 화주사의 이번 달 임시직 데이터가 없습니다.")
else:
    st.error("데이터를 불러올 수 없습니다. 구글 시트의 '화주사' 열 이름을 확인해 주세요.")

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
