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

apply_theme()

# --- 데이터 로드 ---
BASE_URL = "https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv"
URL_DATA = f"{BASE_URL}&sheet={urllib.parse.quote('구글 데이터')}"
URL_TEMP = f"{BASE_URL}&sheet={urllib.parse.quote('임시직')}"

@st.cache_data(ttl=10)
def load_all_data():
    try:
        df = pd.read_csv(URL_DATA, header=1)
        df.columns = df.columns.str.strip()
        df_temp = pd.read_csv(URL_TEMP, header=1)
        df_temp.columns = df_temp.columns.str.strip()
        return df.dropna(subset=['화주사']), df_temp.dropna(subset=['화주사'])
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None, None

def to_n(x):
    try:
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["", "-", "None", "nan", "NaN", "0", "0.0"] else 0
    except: return 0

df, df_temp = load_all_data()

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
        # 홈 화면 (기존 동일)
        st.title("📊 남이천1센터 물동량 Dash Board")
        res = []
        for c in comps:
            cdf = df[df['화주사'] == c]
            v_sum = cdf[t_cols].applymap(to_n).sum().sum()
            res.append({"화주사": c, "월 물동량 합계": v_sum})
        sdf = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['월 물동량 합계'].sum()):,}")
        st.bar_chart(sdf.set_index('화주사'), color="#002D56")
    else:
        # --- 상세 페이지 ---
        menu = st.session_state.sel_comp
        if menu in L_MAP and os.path.exists(os.path.join(L_DIR, L_MAP[menu])):
            st.image(os.path.join(L_DIR, L_MAP[menu]), width=180)
        st.markdown(f"## {menu} 상세 현황")

        def format_final_table(target_df, cols):
            # 숫자 0 -> '-' 변환 함수
            for c in ['월 합계'] + cols:
                target_df[c] = target_df[c].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            return target_df

        # --- 1. 물동량 현황 ---
        st.markdown("#### 1. 물동량 현황")
        cdf = df[df['화주사'] == menu]
        if not cdf.empty:
            orig_order = list(dict.fromkeys(cdf['구분'].dropna().tolist()))
            df_detail = cdf[cdf['구분'].notna()][['구분'] + t_cols].copy()
            for c in t_cols: df_detail[c] = df_detail[c].apply(to_n)
            
            df_grouped = df_detail.groupby('구분', sort=False).sum().reset_index()
            df_grouped['월 합계'] = df_grouped[t_cols].sum(axis=1)
            
            # 표 가공
            dt_final = df_grouped[['구분', '월 합계'] + t_cols].copy()
            new_cols = {c: c.split("-")[-1] for c in t_cols}
            dt_final = dt_final.rename(columns=new_cols)
            
            # 스타일링 (음영)
            styled = dt_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == '월 합계' else '' for _ in x], axis=0)
            st.dataframe(format_final_table(dt_final, list(new_cols.values())), use_container_width=True, hide_index=True)

        # --- 2. 임시직 투입 현황 ---
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if df_temp is not None:
            t_df = df_temp[df_temp['화주사'] == menu]
            if not t_df.empty:
                # 🔥 구분값 강제 고정 (남, 여, 지게차)
                temp_order = ["남", "여", "지게차"]
                t_detail = t_df[t_df['구분'].notna()][['구분'] + t_cols].copy()
                for c in t_cols: t_detail[c] = t_detail[c].apply(to_n)
                
                t_grouped = t_detail.groupby('구분', sort=False).sum().reset_index()
                # 없는 항목은 0으로 채워서 순서 고정
                for item in temp_order:
                    if item not in t_grouped['구분'].values:
                        new_row = {col: 0 for col in t_grouped.columns}
                        new_row['구분'] = item
                        t_grouped = pd.concat([t_grouped, pd.DataFrame([new_row])], ignore_index=True)
                
                t_grouped['구분'] = pd.Categorical(t_grouped['구분'], categories=temp_order, ordered=True)
                t_grouped = t_grouped.sort_values('구분')
                
                # 🔥 월 합계 및 일자별 합계 계산
                t_grouped['월 합계'] = t_grouped[t_cols].sum(axis=1)
                
                # 하단에 '일자별 합계' 행 추가
                sum_row = t_grouped[ ['월 합계'] + t_cols ].sum()
                sum_df = pd.DataFrame([['일자별 합계'] + sum_row.tolist()], columns=['구분', '월 합계'] + t_cols)
                t_final_data = pd.concat([t_grouped[['구분', '월 합계'] + t_cols], sum_df], ignore_index=True)
                
                # 열 이름 변경 (01, 02...)
                t_final_display = t_final_data.rename(columns=new_cols)
                
                # 스타일 적용 (월 합계 음영 + 마지막 행 굵게)
                def style_temp(df_data):
                    styles = pd.DataFrame('', index=df_data.index, columns=df_data.columns)
                    styles['월 합계'] = 'background-color: #F0F2F6; font-weight: bold'
                    styles.iloc[-1, :] = 'background-color: #FFF4F4; font-weight: bold' # 마지막행 강조
                    return styles

                st.dataframe(format_final_table(t_final_display, list(new_cols.values())), use_container_width=True, hide_index=True)
            else:
                st.info("해당 화주사의 임시직 데이터가 없습니다.")

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
