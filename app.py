import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64

# Plotly 체크
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 실시간 물동량 DASH BOARD", layout="wide")

# 2. 이미지 경로 (깃허브 배포용 상대 경로)
LOGO_DIR = "LOGO"
CENTER_IMAGE_PATH = os.path.join(LOGO_DIR, "센터조감도.png")
HANEX_LOGO_PATH = os.path.join(LOGO_DIR, "한익스_LOGO.png")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 3. 디자인 (조감도 배경 + 한익스 테마)
def apply_theme():
    img_b64 = get_image_base64(CENTER_IMAGE_PATH)
    bg_style = ""
    if img_b64:
        bg_style = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(rgba(245, 245, 245, 0.85), rgba(245, 245, 245, 0.85)), 
                              url("data:image/png;base64,{img_b64}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        </style>
        """
    st.markdown(f"""
        {bg_style}
        <style>
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-top: 25px solid #E30613 !important;
            border-bottom: 35px solid #002D56 !important;
        }}
        [data-testid="stMetric"] {{
            background-color: white !important;
            padding: 20px !important;
            border-radius: 15px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            border-left: 8px solid #E30613 !important;
        }}
        .stDataFrame {{ background-color: white !important; border-radius: 15px !important; }}
        h1, h2, h3 {{ color: #002D56 !important; font-weight: 900 !important; }}
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# --- 데이터 로직 ---
SHEET_ID = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
SHEET_NAME = "구글 데이터"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = df.columns.str.strip()
        return df.dropna(subset=['화주사']) if '화주사' in df.columns else df
    except: return None

def to_numeric_safe(x):
    try:
        val = str(x).replace(',', '').strip()
        return float(val) if val not in ["", "-", "None", "nan", "NaN"] else 0
    except: return 0

def format_accounting(x):
    val = to_numeric_safe(x)
    return "-" if val == 0 else f"{int(val):,}"

df = load_data()

if df is not None:
    # 2026-로 시작하는 컬럼만 추출
    all_date_cols = [col for col in df.columns if "2026-" in col]
    auto_companies = list(dict.fromkeys(df['화주사'].tolist()))
    
    # --- 사이드바 ---
    if
