import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# =================================================================
# 1. 페이지 초기 설정 (영진님의 원칙: 기능 누락 절대 금지)
# =================================================================
st.set_page_config(
    page_title="남이천1센터 물동량 Dash Board",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폴더 경로 및 로고 정의 (절대 경로 보존)
LOGO_PATH = "LOGO"
BG_IMG_PATH = os.path.join(LOGO_PATH, "센터조감도.png")
MAIN_LOGO_PATH = os.path.join(LOGO_PATH, "한익스_LOGO.png")

# 화주사 로고 매핑 (누락 시 영진님께 혼남 - 전체 리스트 유지)
LOGO_MAP = {
    "DKSH L&L": "DKSH L&L_LOGO.png", "대호 F&B": "대호 F&B_LOGO.png", "덴비코리아": "덴비_LOGO.png",
    "막시무스코리아": "막시무스코리아.png", "매그니프": "매그니프_LOGO.png", "멘소래담": "멘소래담_LOGO.png",
    "머거본": "머거본_LOGO.png", "바이오포트코리아": "바이오포트코리아_LOGO.png", "시세이도": "시세이도_LOGO.png",
    "유니레버": "유니레버_LOGO.png", "커머스파크": "커머스파크_LOGO.png", "펄세스": "펄세스_LOGO.png",
    "PRODENTI": "프로덴티_LOGO.png", "한국프리오": "한국프리오_LOGO.png", "헨켈홈케어": "헨켈홈케어_LOGO.png",
    "네이처리퍼블릭": "네이처리퍼블릭_LOGO.png"
}

# =================================================================
# 2. 고성능 유틸리티 함수 (이미지 및 영진님의 0점 데이터 정밀 처리)
# =================================================================
def convert_img_to_b64(path):
    """이미지 파일을 Base64로 안전하게 변환"""
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

def extract_pure_number(value):
    """영진님이 0으로 채우신 모든 칸을 정확히 숫자로 인식 (누락 방지)"""
    if pd.isna(value) or str(value).strip() in ["", "-", "None", "nan"]:
        return 0.0
    try:
        # 콤마 제거 및 공백 제거 후 숫자만 추출
        s = str(value).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

@st.cache_data(ttl=1)
def load_google_sheet(sheet_name):
    """구글 시트에서 데이터를 정밀하게 로드하고 매칭 키 생성 (보존)"""
    try:
        sid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        encoded_sheet = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
        
        # 원본 데이터 로드
        raw_data = pd.read_csv(url, header=None, dtype=str)
        
        # '화주사' 텍스트가 있는 행을 헤더로 찾기
        header_row_index = 0
        for i, row in raw_data.iterrows():
            if '화주사' in row.values:
                header_row_index = i
                break
        
        # 실제 데이터 가공
        processed_df = raw_data.iloc[header_row_index+1:].copy()
        processed_df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(raw_data.iloc[header_row_index])]
        
        # 필수 열 필터링 및 매칭용 이름 생성 (공백/대소문자 완전 제거)
        processed_df = processed_df.dropna(subset=['화주사', '구분'])
        processed_df['match_name'] = processed_df['화주사'].astype(str).str.replace(r'\s+', '', regex=True).str.upper()
        
        return processed_df
    except Exception as e:
        st.error(f"시트 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# =================================================================
# 3. CSS 스타일링 (영진님이 원하신 초기 배경 및 투명 버튼 원상복구)
# =================================================================
bg_b64_data = convert_img_to_b64(BG_IMG_PATH)
st.markdown(f"""
<style>
    /* 전체 배경화면 설정 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), url('data:image/png;base64,{bg_b64_data}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    /* 사이드바 홈 로고 클릭 영역 (투명 버튼) */
    .home-overlay {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important;
        color: transparent !important; z-index: 100 !important;
    }}
    /* 화주사 로고 슬라이더 (복원) */
    @keyframes logo_move {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider-container {{ background: white; height: 100px; margin-bottom: 30px; overflow: hidden; position: relative; border-radius: 12px; display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    .slider-track {{ animation: logo_move 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slider-item {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slider-item img {{ max-height: 70px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. 전역 데이터 로드 및 사이드바 제어
# =================================================================
vol_df = load_google_sheet('구글 데이터')
tmp_df = load_google_sheet('임시직')

if not vol_df.empty:
    # 화주사 목록 추출
    company_list = list(dict.fromkeys(vol_df['화주사'].tolist()))
    
    # 세션 상태 초기화 (뷰 전환 용)
    if 'page_view' not in st.session_state: st.session_state.page_view = 'home'
    if 'selected_company' not in st.session_state: st.session_state.selected_company = company_list[0]

    with st.sidebar:
        # 투명 홈 버튼 (한익스 로고 클릭 시 홈으로)
        st.markdown('<div class="home-overlay">', unsafe_allow_html=True)
        if st.button("HOME_BTN"):
            st.session_state.page_view = 'home'
            st.rerun()
        if os.path.exists(MAIN_LOGO_PATH):
            st.image(MAIN_LOGO_PATH, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # 화주사 선택 라디오 (선택 시 즉시 뷰 전환)
        try:
            current_idx = company_list.index(st.session_state.selected_company)
        except:
            current_idx = 0
            
        selected_radio = st.radio("📍 화주사 현황 목록", company_list, index=current_idx if st.session_state.page_view == 'detail' else None)
        if selected_radio:
            st.session_state.page_view = 'detail'
            st.session_state.selected_company = selected_radio
            
        search_month = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        
        # [중요] 날짜 컬럼 추출 (영진님의 요청: 1~31일까지 모든 날짜 데이터 보존)
        all_cols = vol_df.columns.tolist()
        # 숫자만 있는 열을 날짜 열로 간주 (1, 2, 3... 31)
        date_columns = [c for c in all_cols if re.search(r'^\d{1,2}$', str(c).strip())]

    # =================================================================
    # 5. 메인 화면 - [HOME 대시보드]
    # =================================================================
    if st.session_state.page_view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        # 로고 슬라이더 복원
        slides = ""
        for c_name, c_file in LOGO_MAP.items():
            img_b64 = convert_img_to_b64(os.path.join(LOGO_PATH, c_file))
            if img_b64:
                slides += f'<div class="slider-item"><img src="data:image/png;base64,{img_b64}"></div>'
        st.markdown(f'<div class="slider-container"><div class="slider-track">{slides}</div></div>', unsafe_allow_html=True)
        
        # 센터 전체 집계
        total_summary_data = []
        for comp in company_list:
            m_key = re.sub(r'\s+', '', comp).upper()
            # 물동량 합계
            comp_v = vol_df[vol_df['match_name'] == m_key][date_columns].applymap(extract_pure_number).sum().sum()
            # 임시직 합계 (매칭 정밀화)
            comp_t = 0
            if not tmp_df.empty:
                t_sub = tmp_df[tmp_df['match_name'] == m_key]
                t_cols = [tc for tc in date_columns if tc in t_sub.columns]
                comp_t = t_sub[t_cols].applymap(extract_pure_number).sum().sum() if t_cols else 0
            total_summary_data.append({"화주사": comp, "물동량 합계": comp_v, "임시직 합계": comp_t})
        
        summary_df = pd.DataFrame(total_summary_data)
        
        # 센터 전체 물동량 대형 지표 박스
        st.markdown(f"""
            <div style="background-color: #002D56; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700;">
                <h3 style="color: white; margin: 0;">📦 {search_month}월 센터 전체 물동량 총계</h3>
                <h1 style="color: #FFD700; margin: 10px 0; font-size: 3.5rem;">{int(summary_df['물동량 합계'].sum()):,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("#### 📈 화주사별 물동량 분석")
            st.bar_chart(summary_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약 테이블")
            disp_df = summary_df.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                disp_df[col] = disp_df[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(disp_df, use_container_width=True, hide_index=True, height=500)

    # =================================================================
    # 6. 메인 화면 - [상세 페이지: 화주사 클릭 시 물동량/임시직 정밀 복구]
    # =================================================================
    else:
        target = st.session_state.selected_company
        # 우상단 화주사 로고 배치 (보존)
        if target in LOGO_MAP:
            target_b64 = convert_img_to_b64(os.path.join(LOGO_PATH, LOGO_MAP[target]))
            if target_b64:
                st.markdown(f'<div style="position: absolute; top: -10px; right: 20px; z-index: 1000;"><img src="data:image/png;base64,{target_b64}" style="height:60px;"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {target} 상세 실적 분석")
        m_key = re.sub(r'\s+', '', target).upper()

        # --- 1. 물동량 상세 섹션 (음영 처리 100% 보존) ---
        st.markdown("#### 📦 일자별 물동량 현황")
        # 해당 화주사만 필터링 (match_name 기준)
        v_sub = vol_df[vol_df['match_name'] == m_key][['구분'] + date_columns].copy()
        for col in date_columns:
            v_sub[col] = v_sub[col].apply(extract_pure_number)
            
        v_grouped = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_grouped.insert(1, '월 합계', v_grouped[date_columns].sum(axis=1))
        
        # 합계 행 추가 (가장 아래)
        v_sum_row = ['일자별 합계', v_grouped['월 합계'].sum()] + v_grouped[date_columns].sum().tolist()
        v_final = pd.concat([v_grouped, pd.DataFrame([v_sum_row], columns=v_grouped.columns)], ignore_index=True)
        
        st.dataframe(
            v_final.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(v_final)-1 else '' for _ in x], axis=1)
            .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)),
            use_container_width=True, hide_index=True
        )

        # --- 2. 임시직 상세 섹션 (데이터 누락/꼬임 완전 차단) ---
        st.markdown("---")
        st.markdown("#### 👤 일자별 임시직 투입 현황")
        if not tmp_df.empty:
            t_sub = tmp_df[tmp_df['match_name'] == m_key].copy()
            t_category_rows = []
            for cat in ["남", "여", "지게차"]:
                rd = t_sub[t_sub['구분'] == cat]
                # 날짜 열에 맞춰 정확히 데이터 매칭
                vals = [extract_pure_number(rd[c].values[0]) if not rd.empty and c in rd.columns else 0.0 for c in date_columns]
                t_category_rows.append([cat] + vals)
            
            t_df = pd.DataFrame(t_category_rows, columns=['구분'] + date_columns)
            t_df.insert(1, '월 합계', t_df[date_columns].sum(axis=1))
            
            # 합계 행 추가 (음영용)
            t_sum_row = ['일자별 합계', t_df['월 합계'].sum()] + t_df[date_columns].sum().tolist()
            t_final = pd.concat([t_df, pd.DataFrame([t_sum_row], columns=t_df.columns)], ignore_index=True)
            
            st.dataframe(
                t_final.style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(t_final)-1 else '' for _ in x], axis=1)
                .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)),
                use_container_width=True, hide_index=True
            )

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
