import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# =================================================================
# 1. 페이지 초기 설정 및 상수 정의 (글자 수 및 로직 보존)
# =================================================================
st.set_page_config(
    page_title="남이천1센터 물동량 Dash Board",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폴더 및 파일 경로 설정
LOGO_DIR = "LOGO"
CENTER_IMAGE = os.path.join(LOGO_DIR, "센터조감도.png")
HANEX_LOGO = os.path.join(LOGO_DIR, "한익스_LOGO.png")

# 화주사별 로고 매핑 리스트 (단 하나도 빠짐없이 유지)
LOGO_MAP = {
    "DKSH L&L": "DKSH L&L_LOGO.png",
    "대호 F&B": "대호 F&B_LOGO.png",
    "덴비코리아": "덴비_LOGO.png",
    "막시무스코리아": "막시무스코리아.png",
    "매그니프": "매그니프_LOGO.png",
    "멘소래담": "멘소래담_LOGO.png",
    "머거본": "머거본_LOGO.png",
    "바이오포트코리아": "바이오포트코리아_LOGO.png",
    "시세이도": "시세이도_LOGO.png",
    "유니레버": "유니레버_LOGO.png",
    "커머스파크": "커머스파크_LOGO.png",
    "펄세스": "펄세스_LOGO.png",
    "PRODENTI": "프로덴티_LOGO.png",
    "한국프리오": "한국프리오_LOGO.png",
    "헨켈홈케어": "헨켈홈케어_LOGO.png",
    "네이처리퍼블릭": "네이처리퍼블릭_LOGO.png"
}

# =================================================================
# 2. 핵심 유틸리티 함수 (데이터 처리 및 이미지 변환)
# =================================================================
def get_base64_encoded_image(image_path):
    """이미지 파일을 읽어 Base64로 인코딩 (배경 및 CSS 적용용)"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def clean_and_convert_to_float(value):
    """지저분한 문자열에서 숫자만 추출 (중간 누락 방지 핵심 함수)"""
    if pd.isna(value) or str(value).strip() in ["", "-", "None", "nan"]:
        return 0.0
    try:
        # 콤마 제거 및 공백 제거
        cleaned_str = str(value).replace(',', '').strip()
        # 정규표현식으로 숫자와 소수점만 추출
        extracted_numbers = re.findall(r'\d+\.?\d*', cleaned_str)
        if extracted_numbers:
            return float(extracted_numbers[0])
        return 0.0
    except (ValueError, TypeError, IndexError):
        return 0.0

@st.cache_data(ttl=1)
def fetch_google_sheet_data(sheet_name):
    """구글 시트로부터 데이터를 강제로 긁어오고 헤더를 재구성"""
    try:
        spreadsheet_id = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        encoded_sheet_name = urllib.parse.quote(sheet_name)
        csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"
        
        # [중요] 모든 열을 문자열로 읽어서 파이썬이 숫자를 글자로 오해하는 것 차단
        raw_df = pd.read_csv(csv_url, header=None, dtype=str)
        
        # '화주사' 키워드가 있는 행을 찾아 실제 데이터 시작점으로 설정
        header_index = 0
        for i, row in raw_df.iterrows():
            if '화주사' in row.values:
                header_index = i
                break
        
        # 헤더 아래의 실제 데이터 추출
        processed_df = raw_df.iloc[header_index+1:].copy()
        # 컬럼명 설정 (공백 제거 및 결측치 처리)
        processed_df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(raw_df.iloc[header_index])]
        
        # 필수 열이 없는 데이터 제거
        processed_df = processed_df.dropna(subset=['화주사', '구분'])
        # 검색 및 매칭용 이름 열 추가
        processed_df['match_name'] = processed_df['화주사'].astype(str).str.replace(' ', '').str.upper()
        
        return processed_df
    except Exception as e:
        st.error(f"구글 시트 데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# =================================================================
# 3. CSS 스타일링 및 인터페이스 디자인 (풀 버전 서식)
# =================================================================
background_b64 = get_base64_encoded_image(CENTER_IMAGE)
st.markdown(f"""
<style>
    /* 전체 배경화면 설정 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{background_b64}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* 사이드바 홈 로고 클릭용 투명 레이어 버튼 */
    .logo-wrapper {{
        position: relative;
        width: 100%;
        text-align: center;
        margin-bottom: 25px;
    }}
    
    .stButton>button {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 999 !important;
        cursor: pointer !important;
    }}
    
    /* 하단 로고 슬라이더 애니메이션 설정 */
    @keyframes scroll_logos {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(calc(-150px * 8)); }}
    }}
    
    .logo-slider-container {{
        background: white;
        height: 110px;
        margin-bottom: 30px;
        overflow: hidden;
        position: relative;
        border-radius: 12px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    
    .logo-slider-track {{
        animation: scroll_logos 28s linear infinite alternate;
        display: flex;
        width: calc(150px * 16);
    }}
    
    .logo-item {{
        width: 150px;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .logo-item img {{
        max-height: 80px;
        max-width: 100%;
        object-fit: contain;
    }}
    
    /* 상세 페이지용 우측 상단 로고 위치 고정 */
    .top-right-floating-logo {{
        position: absolute;
        top: 0px;
        right: 30px;
        z-index: 1000;
    }}
    
    .top-right-floating-logo img {{
        height: 70px;
        object-fit: contain;
    }}
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. 데이터 로드 및 전처리 수행
# =================================================================
df_vol_main = fetch_google_sheet_data('구글 데이터')
df_temp_main = fetch_google_sheet_data('임시직')

if not df_vol_main.empty:
    # 화주사 목록 추출 (원본 시트 순서 고정)
    company_list = list(dict.fromkeys(df_vol_main['화주사'].tolist()))
    
    # 세션 상태 초기화
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'home'
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = company_list[0]

    # 사이드바 구성
    with st.sidebar:
        # 홈 버튼 (한익스 로고 클릭 기능)
        st.markdown('<div class="logo-wrapper">', unsafe_allow_html=True)
        if st.button("GO_HOME"):
            st.session_state.view_mode = 'home'
            st.rerun()
        if os.path.exists(HANEX_LOGO):
            st.image(HANEX_LOGO, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # 화주사 선택 라디오 버튼 (인덱스 추적)
        try:
            current_comp_idx = company_list.index(st.session_state.selected_company)
        except:
            current_comp_idx = 0
            
        selected_comp = st.radio("📍 화주사 목록", company_list, index=current_comp_idx if st.session_state.view_mode == 'detail' else None)
        
        if selected_comp:
            st.session_state.view_mode = 'detail'
            st.session_state.selected_company = selected_comp
            
        selected_month = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        
        # [데이터 누락 방지 핵심] 날짜 컬럼 식별 (이름이 아닌 위치로 모든 데이터 열 식별)
        all_column_names = df_vol_main.columns.tolist()
        # 제외할 고정 컬럼들
        fixed_cols = ['화주사', '구분', '합계', '계', 'match_name']
        # 날짜 데이터가 들어있는 컬럼들만 추출
        date_data_cols = [c for c in all_column_names if c not in fixed_cols and "Unnamed" not in c and "월합계" not in c]

    # =================================================================
    # 5. 메인 화면 - [메인 대시보드 (HOME)]
    # =================================================================
    if st.session_state.view_mode == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        # 하단 로고 슬라이더 구현
        slider_html_content = ""
        for name, filename in LOGO_MAP.items():
            encoded_logo = get_base64_encoded_image(os.path.join(LOGO_DIR, filename))
            if encoded_logo:
                slider_html_content += f'<div class="logo-item"><img src="data:image/png;base64,{encoded_logo}"></div>'
        
        st.markdown(f'<div class="logo-slider-container"><div class="logo-slider-track">{slider_html_content}</div></div>', unsafe_allow_html=True)
        
        # 요약 데이터 집계 로직
        summary_results = []
        for comp in company_list:
            match_key = comp.replace(' ', '').upper()
            comp_vol_data = df_vol_main[df_vol_main['match_name'] == match_key][date_data_cols]
            total_vol_val = comp_vol_data.applymap(clean_and_convert_to_float).sum().sum()
            
            total_temp_val = 0
            if not df_temp_main.empty:
                temp_data_sub = df_temp_main[df_temp_main['match_name'] == match_key]
                valid_temp_cols = [tc for tc in date_data_cols if tc in temp_data_sub.columns]
                total_temp_val = temp_data_sub[valid_temp_cols].applymap(clean_and_convert_to_float).sum().sum() if valid_temp_cols else 0
            
            summary_results.append({"화주사": comp, "물동량 합계": total_vol_val, "임시직 합계": total_temp_val})
        
        summary_df_final = pd.DataFrame(summary_results)
        grand_total_volume = summary_df_final['물동량 합계'].sum()
        
        # 센터 전체 물동량 대형 지표 (서식 보존)
        st.markdown(f"""
            <div style="background-color: #002D56; padding: 35px; border-radius: 18px; text-align: center; margin-bottom: 35px; box-shadow: 0 6px 20px rgba(0,0,0,0.25);">
                <h2 style="color: #FFFFFF; margin: 0; font-weight: 300;">📦 {selected_month}월 센터 전체 물동량 계</h2>
                <h1 style="color: #FFD700; margin: 15px 0; font-size: 4.5rem; font-weight: 900; letter-spacing: -2px;">{int(grand_total_volume):,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        col_chart, col_table = st.columns([1.6, 1])
        with col_chart:
            st.markdown("#### 📈 화주사별 물동량 분석")
            st.bar_chart(summary_df_final.set_index('화주사')['물동량 합계'], color="#002D56")
        with col_table:
            st.markdown("#### 📋 현황 요약 리스트")
            styled_summary = summary_df_final.copy()
            for col_name in ["물동량 합계", "임시직 합계"]:
                styled_summary[col_name] = styled_summary[col_name].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(styled_summary, use_container_width=True, hide_index=True, height=550)

    # =================================================================
    # 6. 메인 화면 - [상세 현황 대시보드]
    # =================================================================
    else:
        target_company = st.session_state.selected_company
        # 우상단 로고 표시
        if target_company in LOGO_MAP:
            detail_logo_b64 = get_base64_encoded_image(os.path.join(LOGO_DIR, LOGO_MAP[target_company]))
            if detail_logo_b64:
                st.markdown(f'<div class="top-right-floating-logo"><img src="data:image/png;base64,{detail_logo_b64}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {target_company} 상세 실적 현황 ({selected_month}월)")
        search_match_key = target_company.replace(' ', '').upper()

        # --- 1. 물동량 상세 정보 테이블 ---
        st.markdown("#### 1. 일자별 물동량 상세")
        vol_detail_sub = df_vol_main[df_vol_main['match_name'] == search_match_key][['구분'] + date_data_cols].copy()
        for d_col in date_data_cols:
            vol_detail_sub[d_col] = vol_detail_sub[d_col].apply(clean_and_convert_to_float)
            
        vol_grouped = vol_detail_sub.groupby('구분', sort=False).sum().reset_index()
        vol_grouped.insert(1, '월 합계', vol_grouped[date_data_cols].sum(axis=1))
        
        # 하단 전체 합계 행 추가
        vol_total_sum_row = ['일자별 합계', vol_grouped['월 합계'].sum()] + vol_grouped[date_data_cols].sum().tolist()
        vol_display_df = pd.concat([vol_grouped, pd.DataFrame([vol_total_sum_row], columns=vol_grouped.columns)], ignore_index=True)
        
        # 헤더 일자별 넘버링 (1, 2, 3...)
        clean_date_headers = {orig: str(idx+1) for idx, orig in enumerate(date_data_cols)}
        st.dataframe(vol_display_df.rename(columns=clean_date_headers).style.format(lambda val: f"{int(val):,}" if isinstance(val, (float, int)) and val > 0 else ("-" if isinstance(val, (float, int)) else val)), use_container_width=True, hide_index=True)

        # --- 2. 임시직 상세 정보 테이블 ---
        st.markdown("---")
        st.markdown("#### 2. 일자별 임시직 투입 상세")
        if not df_temp_main.empty:
            temp_detail_sub = df_temp_main[df_temp_main['match_name'] == search_match_key].copy()
            
            temp_rows_collector = []
            for category in ["남", "여", "지게차"]:
                category_data = temp_detail_sub[temp_detail_sub['구분'] == category]
                category_vals = [clean_and_convert_to_float(category_data[dc].values[0]) if not category_data.empty and dc in category_data.columns else 0.0 for dc in date_data_cols]
                temp_rows_collector.append([category] + category_vals)
                
            temp_final_df = pd.DataFrame(temp_rows_collector, columns=['구분'] + date_data_cols)
            temp_final_df.insert(1, '월 합계', temp_final_df[date_data_cols].sum(axis=1))
            
            # 하단 전체 합계 행 추가
            temp_total_sum_row = ['일자별 합계', temp_final_df['월 합계'].sum()] + temp_final_df[date_data_cols].sum().tolist()
            temp_display_df = pd.concat([temp_final_df, pd.DataFrame([temp_total_sum_row], columns=temp_final_df.columns)], ignore_index=True)
            
            st.dataframe(temp_display_df.rename(columns=clean_date_headers).style.format(lambda val: f"{int(val):,}" if isinstance(val, (float, int)) and val > 0 else ("-" if isinstance(val, (float, int)) else val)), use_container_width=True, hide_index=True)

# 푸터 영역
st.sidebar.write("---")
st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center | 물동량 관리 시스템 v2.5")
