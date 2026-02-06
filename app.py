import streamlit as st
import pandas as pd
import urllib.parse
import os
import base64
import re

# =================================================================
# 1. 페이지 초기 설정 (전체 레이아웃 및 환경 설정)
# =================================================================
st.set_page_config(
    page_title="남이천1센터 물동량 Dash Board",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폴더 경로 및 파일 정의
LOGO_PATH = "LOGO"
BG_IMG = os.path.join(LOGO_PATH, "센터조감도.png")
MAIN_LOGO = os.path.join(LOGO_PATH, "한익스_LOGO.png")

# 화주사 로고 매핑 (절대 누락 금지)
LOGO_MAP = {
    "DKSH L&L": "DKSH L&L_LOGO.png", "대호 F&B": "대호 F&B_LOGO.png", "덴비코리아": "덴비_LOGO.png",
    "막시무스코리아": "막시무스코리아.png", "매그니프": "매그니프_LOGO.png", "멘소래담": "멘소래담_LOGO.png",
    "머거본": "머거본_LOGO.png", "바이오포트코리아": "바이오포트코리아_LOGO.png", "시세이도": "시세이도_LOGO.png",
    "유니레버": "유니레버_LOGO.png", "커머스파크": "커머스파크_LOGO.png", "펄세스": "펄세스_LOGO.png",
    "PRODENTI": "프로덴티_LOGO.png", "한국프리오": "한국프리오_LOGO.png", "헨켈홈케어": "헨켈홈케어_LOGO.png",
    "네이처리퍼블릭": "네이처리퍼블릭_LOGO.png"
}

# =================================================================
# 2. 고성능 유틸리티 함수 (이미지 및 데이터 정밀 처리)
# =================================================================
def convert_image_to_base64(path):
    """이미지를 Base64로 변환하여 CSS에서 사용 가능하게 함"""
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

def extract_pure_number(value):
    """모든 방해 요소를 제거하고 순수 숫자만 추출 (누락 방지)"""
    if pd.isna(value) or str(value).strip() in ["", "-", "None", "nan"]:
        return 0.0
    try:
        s = str(value).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

@st.cache_data(ttl=1)
def load_sheet_data(sheet_name):
    """구글 시트에서 데이터를 정밀하게 로드 (헤더 자동 감지 및 문자열 강제화)"""
    try:
        sid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        encoded_name = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        
        # 1차 로드 (데이터 구조 파악)
        raw = pd.read_csv(url, header=None, dtype=str)
        
        # '화주사' 위치 찾기
        h_idx = 0
        for i, row in raw.iterrows():
            if '화주사' in row.values:
                h_idx = i
                break
        
        # 2차 가공 (실제 데이터와 헤더 결합)
        df = raw.iloc[h_idx+1:].copy()
        df.columns = [str(c).strip() if pd.notna(c) else f"col_{idx}" for idx, c in enumerate(raw.iloc[h_idx])]
        
        # 공백 제거 및 필수값 필터링
        df = df.dropna(subset=['화주사', '구분'])
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '').str.upper()
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# =================================================================
# 3. CSS 스타일링 (배경, 투명버튼, 슬라이더, 음영)
# =================================================================
bg_b64 = convert_image_to_base64(BG_IMG)
st.markdown(f"""
<style>
    /* 배경 설정 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), url('data:image/png;base64,{bg_b64}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    /* 사이드바 홈 로고 클릭 레이어 */
    .home-logo-overlay {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important;
        color: transparent !important; z-index: 100 !important;
    }}
    /* 로고 슬라이더 애니메이션 */
    @keyframes move_logos {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider-box {{ background: white; height: 100px; margin-bottom: 30px; overflow: hidden; position: relative; border-radius: 12px; display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    .slider-track {{ animation: move_logos 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide-item {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slide-item img {{ max-height: 70px; object-fit: contain; }}
    /* 우상단 고정 로고 */
    .floating-logo {{ position: absolute; top: -10px; right: 20px; z-index: 1000; }}
    .floating-logo img {{ height: 60px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# =================================================================
# 4. 데이터 로드 및 전역 변수 설정
# =================================================================
df_vol = load_sheet_data('구글 데이터')
df_tmp = load_sheet_data('임시직')

if not df_vol.empty:
    # 화주사 리스트 (원본 순서 유지)
    comp_list = list(dict.fromkeys(df_vol['화주사'].tolist()))
    
    if 'view' not in st.session_state: st.session_state.view = 'home'
    if 'sel_comp' not in st.session_state: st.session_state.sel_comp = comp_list[0]

    with st.sidebar:
        # 투명 홈 버튼 구현
        st.markdown('<div class="home-logo-overlay">', unsafe_allow_html=True)
        if st.button("HOME_CLICK"):
            st.session_state.view = 'home'
            st.rerun()
        if os.path.exists(MAIN_LOGO): st.image(MAIN_LOGO, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # 화주사 선택 메뉴
        c_idx = comp_list.index(st.session_state.sel_comp) if st.session_state.sel_comp in comp_list else 0
        sel = st.radio("📍 화주사 현황 목록", comp_list, index=c_idx if st.session_state.view == 'detail' else None)
        if sel:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = sel
            
        target_mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        
        # [중요] 날짜 컬럼 식별 로직 (1월 8일 이후 데이터 누락 방지)
        all_cols = df_vol.columns.tolist()
        # '화주사', '구분', '합계', 'match_name' 등을 제외한 모든 열을 날짜 데이터로 간주
        date_cols = [c for c in all_cols if c not in ['화주사', '구분', '합계', '계', '비고', 'match_name'] and "Unnamed" not in c]

    # =================================================================
    # 5. 메인 화면 - [HOME 대시보드]
    # =================================================================
    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        # 로고 슬라이더 복구
        slides_html = ""
        for name, file in LOGO_MAP.items():
            b64 = convert_image_to_base64(os.path.join(LOGO_PATH, file))
            if b64: slides_html += f'<div class="slide-item"><img src="data:image/png;base64,{b64}"></div>'
        st.markdown(f'<div class="slider-box"><div class="slider-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        # 전체 데이터 집계
        total_summary = []
        for c in comp_list:
            m_key = c.replace(' ', '').upper()
            c_v_data = df_vol[df_vol['match_name'] == m_key][date_cols]
            v_sum = c_v_data.applymap(extract_pure_number).sum().sum()
            
            t_sum = 0
            if not df_tmp.empty:
                # 임시직 데이터 매칭 로직 복구
                t_sub = df_tmp[df_tmp['match_name'] == m_key]
                act_t_cols = [tc for tc in date_cols if tc in t_sub.columns]
                t_sum = t_sub[act_t_cols].applymap(extract_pure_number).sum().sum() if act_t_cols else 0
            
            total_summary.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        sum_df = pd.DataFrame(total_summary)
        all_v_total = sum_df['물동량 합계'].sum()
        
        # 센터 전체 물동량 대형 지표 (서식 및 음영 강조)
        st.markdown(f"""
            <div style="background-color: #002D56; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; border: 3px solid #FFD700;">
                <h2 style="color: #FFFFFF; margin: 0;">📦 {target_mon}월 센터 전체 물동량 합계</h2>
                <h1 style="color: #FFD700; margin: 10px 0; font-size: 4rem;">{int(all_v_total):,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("#### 📈 화주사별 물동량 분석")
            st.bar_chart(sum_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            disp_sum = sum_df.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                disp_sum[col] = disp_sum[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(disp_sum, use_container_width=True, hide_index=True, height=500)

    # =================================================================
    # 6. 메인 화면 - [상세 페이지 (음영 및 서식 복구)]
    # =================================================================
    else:
        target_c = st.session_state.sel_comp
        if target_c in LOGO_MAP:
            d_logo = convert_image_to_base64(os.path.join(LOGO_PATH, LOGO_MAP[target_c]))
            if d_logo: st.markdown(f'<div class="floating-logo"><img src="data:image/png;base64,{d_logo}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### 🏢 {target_c} 상세 현황")
        m_key = target_c.replace(' ', '').upper()

        # 표 음영 처리를 위한 스타일 함수
        def style_sum_rows(s):
            return ['background-color: #E6F3FF; font-weight: bold' if s.name == len(v_final)-1 else '' for _ in s]

        # --- 1. 물동량 상세 (음영 및 서식 복구) ---
        v_sub = df_vol[df_vol['match_name'] == m_key][['구분'] + date_cols].copy()
        for col in date_cols: v_sub[col] = v_sub[col].apply(extract_pure_number)
        
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g.insert(1, '월 합계', v_g[date_cols].sum(axis=1))
        
        v_total_row = ['일자별 합계', v_g['월 합계'].sum()] + v_g[date_cols].sum().tolist()
        v_final = pd.concat([v_g, pd.DataFrame([v_total_row], columns=v_g.columns)], ignore_index=True)
        
        st.markdown("#### 1. 일자별 물동량 현황")
        # 헤더 정비 및 음영 적용
        v_disp = v_final.rename(columns={c: str(idx+1) for idx, c in enumerate(date_cols)})
        st.dataframe(
            v_disp.style.apply(lambda x: ['background-color: #002D56; color: white; font-weight: bold' if x.name == len(v_final)-1 else '' for _ in x], axis=1)
            .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)),
            use_container_width=True, hide_index=True
        )

        # --- 2. 임시직 상세 (연동 및 음영 복구) ---
        st.markdown("---")
        st.markdown("#### 2. 일자별 임시직 투입 현황")
        if not df_tmp.empty:
            t_sub = df_tmp[df_tmp['match_name'] == m_key].copy()
            t_rows = []
            for cat in ["남", "여", "지게차"]:
                rd = t_sub[t_sub['구분'] == cat]
                vals = [extract_pure_number(rd[c].values[0]) if not rd.empty and c in rd.columns else 0.0 for c in date_cols]
                t_rows.append([cat] + vals)
            
            t_df = pd.DataFrame(t_rows, columns=['구분'] + date_cols)
            t_df.insert(1, '월 합계', t_df[date_cols].sum(axis=1))
            t_total_row = ['일자별 합계', t_df['월 합계'].sum()] + t_df[date_cols].sum().tolist()
            t_final = pd.concat([t_df, pd.DataFrame([t_total_row], columns=t_df.columns)], ignore_index=True)
            
            st.dataframe(
                t_final.rename(columns={c: str(idx+1) for idx, c in enumerate(date_cols)})
                .style.apply(lambda x: ['background-color: #F0F2F6; font-weight: bold' if x.name == len(t_final)-1 else '' for _ in x], axis=1)
                .format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)),
                use_container_width=True, hide_index=True
            )

st.sidebar.write("---")
st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
