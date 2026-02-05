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
st.set_page_config(page_title="남이천1센터 실시간 물동량 관리", layout="wide")

# 2. 이미지 경로 (깃허브 배포를 위해 'LOGO' 폴더 상대경로로 수정)
LOGO_DIR = "LOGO"
CENTER_IMAGE_PATH = os.path.join(LOGO_DIR, "센터조감도.png")
HANEX_LOGO_PATH = os.path.join(LOGO_DIR, "한익스_LOGO.png")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 3. 디자인 (조감도 배경 + 한익스 테마 복구)
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
    all_date_cols = [col for col in df.columns if "2026-" in col]
    auto_companies = list(dict.fromkeys(df['화주사'].tolist()))
    
    # --- 사이드바 ---
    if os.path.exists(HANEX_LOGO_PATH):
        st.sidebar.image(HANEX_LOGO_PATH, use_container_width=True)
    
    menu = st.sidebar.radio("📍 메뉴 선택", ["🏠 전체 요약"] + auto_companies)
    selected_month = st.sidebar.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
    target_month = f"2026-{selected_month}"
    current_month_cols = [col for col in all_date_cols if col.startswith(target_month)]
    display_date_map = {col: col.replace("2026-", "") for col in current_month_cols}

    # --- 메인 화면 ---
    if menu == "🏠 전체 요약":
        st.markdown(f"## 🚀 {selected_month}월 종합 모니터링")
        summary_data = []
        for com in auto_companies:
            c_df = df[df['화주사'] == com]
            def get_val(keys):
                if '구분' in c_df.columns:
                    mask = c_df['구분'].str.replace(" ", "").str.contains('|'.join(keys), na=False, case=False)
                    return c_df[mask][current_month_cols].applymap(to_numeric_safe).sum().sum()
                return 0
            vol, sales, costs = get_val(["물동량", "입고", "출고", "반품"]), get_val(["매출"]), get_val(["비용"])
            summary_data.append({"화주사": com, "물동량": vol, "매출": sales, "비용": costs, "이익": sales - costs})
        
        sum_df = pd.DataFrame(summary_data)
        m1, m2, m3 = st.columns(3)
        m1.metric("📦 총 물동량", f"{int(sum_df['물동량'].sum()):,}")
        m2.metric("💰 총 매출액", f"{int(sum_df['매출'].sum()):,}원")
        m3.metric("📈 총 이익액", f"{int(sum_df['이익'].sum()):,}원")
        
        st.markdown("### 📋 화주별 실적 요약")
        disp_sum = sum_df.copy()
        for col in ["물동량", "매출", "비용", "이익"]:
            disp_sum[col] = disp_sum[col].apply(format_accounting)
        st.dataframe(disp_sum, use_container_width=True, hide_index=True)

    else:
        # 업체별 상세 로고
        LOGO_MAP = {
            "DKSH L&L": "DKSH L&L_LOGO.png", "대호 F&B": "대호 F&B_LOGO.png", "덴비코리아": "덴비_LOGO.png",
            "막시무스코리아": "막시무스_LOGO.png", "매그니프": "매그니프_LOGO.png", "멘소래담": "멘소래담_LOGO.png", 
            "머거본": "머거본_LOGO.png", "바이오포트코리아": "바이오포트코리아_LOGO.png", "시세이도": "시세이도_LOGO.png",
            "유니레버": "유니레버_LOGO.png", "커머스파크": "커머스파크_LOGO.png", "펄세스": "펄세스_LOGO.png",
            "프로덴티": "프로덴티_LOGO.png", "한국프리오": "한국프리오_LOGO.png", "헨켈홈케어": "헨켈홈케어_LOGO.png"
        }
        logo_f = LOGO_MAP.get(menu)
        if logo_f:
            full_path = os.path.join(LOGO_DIR, logo_f)
            if os.path.exists(full_path):
                st.image(full_path, width=150)
        
        st.markdown(f"## {menu}")
        comp_df = df[df['화주사'] == menu]
        if not comp_df.empty:
            vol_mask = comp_df['구분'].str.replace(" ", "").str.contains('물동량|입고|출고|반품', na=False, case=False)
            daily_vol = comp_df[vol_mask][current_month_cols].applymap(to_numeric_safe).sum().reset_index()
            daily_vol.columns = ["날짜", "물동량"]
            daily_vol["날짜"] = daily_vol["날짜"].str.replace("2026-", "")
            
            if HAS_PLOTLY:
                fig = px.area(daily_vol, x="날짜", y="물동량", title=f"📈 {selected_month}월 물동량 추이")
                fig.update_traces(line_color='#E30613', fillcolor='rgba(227, 6, 19, 0.2)')
                fig.update_layout(plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', font_color="#002D56")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.area_chart(daily_vol.set_index("날짜"), color="#E30613")
            
            st.markdown("### 📂 상세 데이터")
            detail_t = comp_df[["구분"] + current_month_cols].copy()
            for col in current_month_cols:
                detail_t[col] = detail_t[col].apply(format_accounting)
            st.dataframe(detail_t.rename(columns=display_date_map), use_container_width=True, hide_index=True)

st.sidebar.caption(f"© 2026 HanExpress Nam-Icheon Center")