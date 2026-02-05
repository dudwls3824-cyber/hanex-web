import streamlit as st
import pandas as pd
import urllib.parse, os, base64

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 이미지 및 로고 경로 설정
L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")

def get_b64(p):
    if os.path.exists(p):
        return base64.b64encode(open(p, "rb").read()).decode()
    return None

# 3. 디자인 테마 (화면 상단 코드 노출 오류 해결)
def apply_theme():
    b64 = get_b64(C_IMG)
    # 배경 이미지 스타일
    bg_css = f"""
    <style>
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                          url('data:image/png;base64,{b64}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    """ if b64 else "<style>"
    
    # 사이드바 및 메트릭 스타일 통합
    st.markdown(bg_css + """
        [data-testid='stSidebar'] { background-color: #FFFFFF !important; border-top: 25px solid #E30613 !important; border-bottom: 35px solid #002D56 !important; }
        [data-testid='stMetric'] { background-color: white !important; padding: 20px !important; border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important; border-left: 8px solid #E30613 !important; }
        h1, h2, h3 { color: #002D56 !important; font-weight: 900 !important; }
        .stDataFrame { background-color: white !important; border-radius: 10px !important; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# --- 데이터 로드 ---
URL = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('구글 데이터')}"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = df.columns.str.strip()
        return df.dropna(subset=['화주사']) if '화주사' in df.columns else df
    except: return None

def to_n(x):
    try:
        v = str(x).replace(',', '').strip()
        return float(v) if v not in ["", "-", "None", "nan", "NaN"] else 0
    except: return 0

df = load_data()

if df is not None:
    cols2026 = [c for c in df.columns if "2026-" in c]
    comps = list(dict.fromkeys(df['화주사'].tolist()))
    if os.path.exists(H_LOG): st.sidebar.image(H_LOG, use_container_width=True)
    
    # 사이드바 메뉴 구성
    menu = st.sidebar.radio("📍 메뉴 선택", ["🏠 전체 요약"] + comps)
    mon = st.sidebar.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
    t_cols = [c for c in cols2026 if c.startswith(f"2026-{mon}")]

    if menu == "🏠 전체 요약":
        st.title("📊 남이천1센터 물동량 Dash Board")
        st.markdown(f"### 🚀 {mon}월 물동량 종합 현황")
        res = []
        for c in comps:
            cdf = df[df['화주사'] == c]
            m = cdf['구분'].str.replace(" ","").str.contains('물동량|입고|출고|반품', na=False, case=False)
            v_sum = cdf[m][t_cols].applymap(to_n).sum().sum()
            res.append({"화주사": c, "월 물동량 합계": v_sum})
        
        sdf = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['월 물동량 합계'].sum()):,}")
        
        st.markdown("#### 📈 화주사별 물동량 분석")
        st.bar_chart(sdf.set_index('화주사'))
        st.dataframe(sdf.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x), use_container_width=True, hide_index=True)

    else:
        # 상세 페이지 디자인 유지
        L_MAP = {"DKSH L&L":"DKSH L&L_LOGO.png","대호 F&B":"대호 F&B_LOGO.png","덴비코리아":"덴비_LOGO.png","막시무스코리아":"막시무스_LOGO.png","매그니프":"매그니프_LOGO.png","멘소래담":"멘소래담_LOGO.png","머거본":"머거본_LOGO.png","바이오포트코리아":"바이오포트코리아_LOGO.png","시세이도":"시세이도_LOGO.png","유니레버":"유니레버_LOGO.png","커머스파크":"커머스파크_LOGO.png","펄세스":"펄세스_LOGO.png","프로덴티":"프로덴티_LOGO.png","한국프리오":"한국프리오_LOGO.png","헨켈홈케어":"헨켈홈케어_LOGO.png"}
        if menu in L_MAP:
            p = os.path.join(L_DIR, L_MAP[menu])
            if os.path.exists(p): st.image(p, width=150)
        
        st.markdown(f"## {menu} 상세 현황")
        cdf = df[df['화주사'] == menu]
        if not cdf.empty:
            vm = cdf['구분'].str.replace(" ","").str.contains('물동량|입고|출고|반품', na=False, case=False)
            dv = cdf[vm][t_cols].applymap(to_n).sum().reset_index()
            dv.columns = ["날짜", "물동량"]
            dv["날짜"] = dv["날짜"].apply(lambda x: x.split("-")[-1])
            
            st.area_chart(dv.set_index("날짜"), color="#E30613")
            
            dt = cdf[vm][["구분"] + t_cols].copy()
            for c in t_cols: dt[c] = dt[c].apply(lambda x: f"{int(to_n(x)):,}" if to_n(x) != 0 else "-")
            st.dataframe(dt.rename(columns=lambda x: x.split("-")[-1] if "2026-" in x else x), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
