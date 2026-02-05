import streamlit as st
import pandas as pd
import urllib.parse
import re
import os

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 실시간 물동량 관리", layout="wide")

# 2. 로고 폴더 경로 설정 (상대 경로)
# 내 PC와 깃허브 서버 양쪽에서 'app.py'와 같은 위치의 LOGO 폴더를 찾습니다.
LOGO_DIR = "LOGO"

# 화주사명과 로고 파일명 매칭
LOGO_MAP = {
    "DKSH L&L": "DKSH L&L_LOGO.png",
    "대호 F&B": "대호 F&B_LOGO.png",
    "덴비코리아": "덴비_LOGO.png",
    "막시무스코리아": "막시무스_LOGO.png",
    "매그니프": "매그니프_LOGO.png",
    "멘소래담": "멘소래담_LOGO.png", 
    "머거본": "머거본_LOGO.png",
    "바이오포트코리아": "바이오포트코리아_LOGO.png",
    "시세이도": "시세이도_LOGO.png",
    "유니레버": "유니레버_LOGO.png",
    "커머스파크": "커머스파크_LOGO.png",
    "펄세스": "펄세스_LOGO.png",
    "프로덴티": "프로덴티_LOGO.png",
    "한국프리오": "한국프리오_LOGO.png",
    "헨켈홈케어": "헨켈홈케어_LOGO.png"
}

# 3. 데이터 로드 (구글 시트)
SHEET_ID = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
SHEET_NAME = "구글 데이터"
encoded_sheet_name = urllib.parse.quote(SHEET_NAME)
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = df.columns.str.strip()
        if '화주사' in df.columns:
            df = df.dropna(subset=['화주사'])
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

def to_numeric_safe(x):
    if pd.isna(x) or x == "" or x == "-": return 0
    if isinstance(x, (int, float)): return x
    try:
        clean_x = str(x).replace(',', '').replace(' ', '').strip()
        return float(clean_x) if clean_x else 0
    except: return 0

def format_accounting(x):
    val = to_numeric_safe(x)
    return "-" if val == 0 else f"{int(val):,}"

df = load_data()

if df is not None:
    all_date_cols = [col for col in df.columns if "2026-" in col]
    
    # --- 사이드바 (한익스 로고 고정) ---
    hanex_logo_path = os.path.join(LOGO_DIR, "한익스_LOGO.png")
    if os.path.exists(hanex_logo_path):
        st.sidebar.image(hanex_logo_path, use_container_width=True)
    
    st.sidebar.title("📊 물동량 관리 시스템")
    
    auto_companies = list(dict.fromkeys(df['화주사'].tolist()))
    menu = st.sidebar.radio("업체 선택", ["🏠 전체 요약"] + auto_companies)
    
    selected_month = st.sidebar.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
    target_month = f"2026-{selected_month}"
    current_month_cols = [col for col in all_date_cols if col.startswith(target_month)]
    display_date_map = {col: col.replace("2026-", "") for col in current_month_cols}

    # --- 메인 화면 ---
    if menu == "🏠 전체 요약":
        st.title(f"🚀 {selected_month}월 화주별 요약")
        summary_list = []
        for com in auto_companies:
            comp_df = df[df['화주사'] == com]
            def get_sum_val(keywords):
                if '구분' in comp_df.columns:
                    mask = comp_df['구분'].str.replace(" ", "").str.contains('|'.join(keywords), na=False, case=False)
                    rows = comp_df[mask]
                    return rows[current_month_cols].applymap(to_numeric_safe).sum().sum()
                return 0
            
            vol = get_sum_val(["물동량", "입고", "출고", "반품"])
            sales = get_sum_val(["매출"])
            costs = get_sum_val(["비용"])
            summary_list.append({"화주사": com, "물동량": vol, "매출": sales, "비용": costs, "차이": sales - costs})
        
        sum_df = pd.DataFrame(summary_list)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("총 물동량 합계", f"{int(sum_df['물동량'].sum()):,}")
        with col2: st.metric("총 매출 합계", f"{int(sum_df['매출'].sum()):,}원")
        with col3: st.metric("총 이익 합계", f"{int(sum_df['차이'].sum()):,}원")
        
        st.divider()
        st.subheader("📋 업체별 실적 요약")
        display_sum_df = sum_df.copy()
        for c in ["물동량", "매출", "비용", "차이"]:
            display_sum_df[c] = display_sum_df[c].apply(format_accounting)
        st.dataframe(display_sum_df, use_container_width=True, hide_index=True)

    else:
        # 업체별 상세 로고 (제목 위)
        logo_file = LOGO_MAP.get(menu)
        if logo_file:
            full_path = os.path.join(LOGO_DIR, logo_file)
            if os.path.exists(full_path):
                st.image(full_path, width=150)
        
        st.markdown(f"### {menu} 상세 내역")
        st.divider()

        comp_df = df[df['화주사'] == menu]
        if not comp_df.empty:
            daily_trends = comp_df[current_month_cols].applymap(to_numeric_safe).sum()
            daily_trends.index = [d.replace("2026-", "") for d in daily_trends.index]
            st.line_chart(daily_trends)
            
            st.write(f"📂 **항목별 상세 내역 (구분 기준)**")
            if '구분' in comp_df.columns:
                detail_table = comp_df[["구분"] + current_month_cols].copy()
                for col in current_month_cols:
                    detail_table[col] = detail_table[col].apply(format_accounting)
                detail_table = detail_table.rename(columns=display_date_map)
                st.dataframe(detail_table, use_container_width=True, hide_index=True)

st.sidebar.caption(f"© 2026 남이천1센터 물동량 | {selected_month}월")