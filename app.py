import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64

# 1. 페이지 설정 (탭 제목 및 레이아웃)
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 이미지 경로 설정
LOGO_DIR = "LOGO"
CENTER_IMAGE_PATH = os.path.join(LOGO_DIR, "센터조감도.png")
HANEX_LOGO_PATH = os.path.join(LOGO_DIR, "한익스_LOGO.png")

def get_image_base64(path):
    if os.path.exists(path):
        return base64.b64encode(open(path, "rb").read()).decode()
    return None

# 3. 디자인 (조감도 배경 + 한익스 테마)
def apply_theme():
    img_b64 = get_image_base64(CENTER_IMAGE_PATH)
    bg_style = f"""<style>[data-testid="stAppViewContainer"] {{ background-image: linear-gradient(rgba(245, 245, 245, 0.85), rgba(245, 245, 245, 0.85)), url("data:image/png;base64,{img_b64}"); background-size: cover; background-position: center; background-attachment: fixed; }}</style>""" if img_b64 else ""
    st.markdown(bg_style + """<style>[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-top: 25px solid #E30613 !important; border-bottom: 35px solid #002D56 !important; } [data-testid="stMetric"] { background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; } h1, h2, h3 { color: #002D56 !important; font-weight: 900 !important; }</style>""", unsafe_allow_html=True)

apply_theme()

# --- 데이터 로직 ---
URL = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('구글 데이터')}"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = df.columns.str.strip()
        return df.dropna(subset=['화주사']) if '화주사' in df.columns else df
    except: return None

def to_num(x):
    try:
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["", "-", "None", "nan", "NaN"] else 0
    except: return 0

df = load_data()

if df is not None:
    all_dates = [c for c in df.columns if "2026-" in c]
    companies = list(dict.fromkeys(df['화주사'].tolist()))
    
    # 사이드바 상단 로고
    if os.path.exists(HANEX_LOGO_PATH): 
        st.sidebar.image(HANEX_LOGO_PATH, use_container_width=True)
    
    # 수정된 메인 제목 표시
    st.title("📊 남이천1센터 물동량 Dash Board")
    
    menu = st.sidebar.radio("📍 메뉴 선택", ["🏠 전체 요약"] + companies)
    mon = st.sidebar.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
    target_cols = [c for c in all_dates if c.startswith(f"2026-{mon}")]

    if menu == "🏠 전체 요약":
        st.markdown(f"### 🚀 {mon}월 종합 모니터링")
        summary = []
        for com in companies:
            c_df = df[df['화주사'] == com]
            def gv(k):
                m = c_df['구분'].str.replace(" ", "").str.contains('|'.join(k), na=False, case=False)
                return c_df[m][target
