import streamlit as st
import pandas as pd
import urllib.parse, os, base64, re

# ==========================================
# 1. 페이지 설정 및 로고/이미지 매핑
# ==========================================
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")

# 화주사별 로고 매핑 (이름 하나하나 대조하여 누락 방지)
L_MAP = {
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

# ==========================================
# 2. 유틸리티 함수 (데이터 및 이미지 처리)
# ==========================================
def get_b64(path):
    """이미지를 base64로 변환 (CSS 배경 및 로고용)"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_num(x):
    """지저분한 텍스트에서 숫자만 강제로 추출 (중간에 데이터 생겨도 인식)"""
    if pd.isna(x) or str(x).strip() == "" or str(x).strip() == "-":
        return 0
    try:
        s = str(x).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0
    except:
        return 0

@st.cache_data(ttl=1)
def fetch_data(sheet_name):
    """구글 시트에서 데이터를 무조건 긁어옴"""
    try:
        gsid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        url = f"https://docs.google.com/spreadsheets/d/{gsid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        
        # [데이터 누락 방지] 모든 열을 일단 문자열(str)로 읽어야 중간에 숫자가 나와도 안 씹힘
        df = pd.read_csv(url, dtype=str)
        
        # 화주사 컬럼을 기준으로 헤더 위치 조정
        if '화주사' not in df.columns:
            for i in range(min(len(df), 15)):
                if '화주사' in df.iloc[i].values:
                    df = pd.read_csv(url, header=i+1, dtype=str)
                    break
        
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['화주사', '구분'])
        # 매칭용 화주사명 (공백 제거 및 대문자)
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '').str.upper()
        return df
    except Exception as e:
        st.error(f"시트 로드 오류: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CSS 스타일링 (배경, 애니메이션, 투명버튼)
# ==========================================
b64_bg = get_b64(C_IMG)
st.markdown(f"""
<style>
    /* 전체 배경 설정 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{b64_bg}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    /* 사이드바 홈 로고 클릭용 투명 버튼 */
    .logo-container {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important;
        color: transparent !important; z-index: 10 !important; cursor: pointer !important;
    }}
    /* 로고 슬라이더 애니메이션 */
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin-bottom: 25px; overflow: hidden; position: relative; border-radius: 10px; display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
    .slide-track {{ animation: scroll 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slide img {{ max-height: 80px; width: auto; object-fit: contain; }}
    /* 상세 페이지용 우상단 화주사 로고 */
    .top-right-logo {{ position: absolute; top: 0px; right: 20px; z-index: 100; }}
    .top-right-logo img {{ height: 65px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 데이터 로딩 및 사이드바 구성
# ==========================================
df_vol = fetch_data('구글 데이터')
df_temp = fetch_data('임시직')

if not df_vol.empty:
    # 화주사 리스트 추출 (시트 원본 순서 100% 유지)
    comps = list(dict.fromkeys(df_vol['화주사'].tolist()))
    
    if 'view' not in st.session_state:
        st.session_state.view = 'home'

    with st.sidebar:
        # 한익스 로고 위 투명 버튼 설정
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if st.button("HOME_BTN_CLICK"): 
            st.session_state.view = 'home'
            st.rerun()
        if os.path.exists(H_LOG):
            st.image(H_LOG, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # 화주사 목록 라디오 버튼
        curr_idx = comps.index(st.session_state.sel_comp) if ('sel_comp' in st.session_state and st.session_state.sel_comp in comps) else None
        selected = st.radio("📍 화주사 목록", comps, index=curr_idx if st.session_state.view == 'detail' else None)
        
        if selected:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = selected
            
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        
        # [날짜 누락 방지 핵심 로직] 헤더의 숫자(1, 2...)와 날짜 형식(2026-01-01) 모두 식별
        all_cols = df_vol.columns.tolist()
        # 정규식을 사용해 날짜 또는 일자(숫자)만 컬럼으로 추출
        t_cols = [c for c in all_cols if re.search(r'(\d{2,4}[./-]\d{2}[./-]\d{2})|^\d{1,2}$', c)]
        # 선택한 월에 맞는 컬럼만 필터링 (컬럼명이 짧은 숫자면 그대로 사용)
        t_cols = [c for c in t_cols if len(c) <= 2 or f"-{mon}-" in c or c.startswith(f"2026-{mon}")]

    # ==========================================
    # 5. 메인 화면 - [HOME 페이지]
    # ==========================================
    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        # 하단 로고 슬라이더 복구
        slides_html = ""
        for name, file in L_MAP.items():
            b64 = get_b64(os.path.join(L_DIR, file))
            if b64:
                slides_html += f'<div class="slide"><img src="data:image/png;base64,{b64}"></div>'
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        # 전체 데이터 집계 계산
        res_list = []
        for c in comps:
            m_name = c.replace(' ', '').upper()
            # 물동량 합계 (중간에 데이터가 생겨도 무조건 합산)
            v_rows = df_vol[df_vol['match_name'] == m_name][t_cols]
            v_sum = v_rows.applymap(clean_num).sum().sum()
            
            # 임시직 합계
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                t_cols_act = [col for col in t_cols if col in df_temp.columns]
                t_sum = t_sub[t_cols_act].applymap(clean_num).sum().sum() if t_cols_act else 0
            
            res_list.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        summary_df = pd.DataFrame(res_list)
        total_volume = summary_df['물동량 합계'].sum()
        
        # 📦 센터 전체 물동량 대형 지표 (파란 박스 서식)
        st.markdown(f"""
            <div style="background-color: #002D56; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <h2 style="color: white; margin: 0; font-weight: 300;">📦 {mon}월 센터 전체 물동량 계</h2>
                <h1 style="color: #FFD700; margin: 15px 0; font-size: 4rem; font-weight: 800;">{int(total_volume):,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("#### 📈 화주사별 물동량 분석")
            st.bar_chart(summary_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            sdf_disp = summary_df.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_disp[col] = sdf_disp[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_disp, use_container_width=True, hide_index=True, height=520)

    # ==========================================
    # 6. 메인 화면 - [상세 현황 페이지]
    # ==========================================
    else:
        menu_comp = st.session_state.sel_comp
        # 우상단 화주사 로고 표시 로직
        if menu_comp in L_MAP:
            b64_detail = get_b64(os.path.join(L_DIR, L_MAP[menu_comp]))
            if b64_detail:
                st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_detail}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### {menu_comp} 상세 현황 ({mon}월)")
        match_n = menu_comp.replace(' ', '').upper()

        # --- 물동량 상세 테이블 구성 ---
        vol_sub = df_vol[df_vol['match_name'] == match_n][['구분'] + t_cols].copy()
        for col in t_cols:
            vol_sub[col] = vol_sub[col].apply(clean_num)
        
        vol_grp = vol_sub.groupby('구분', sort=False).sum().reset_index()
        vol_grp.insert(1, '월 합계', vol_grp[t_cols].sum(axis=1))
        
        # 가로/세로 합계 행 계산 및 추가
        v_total_line = ['일자별 합계', vol_grp['월 합계'].sum()] + vol_grp[t_cols].sum().tolist()
        v_final_table = pd.concat([vol_grp, pd.DataFrame([v_total_line], columns=vol_grp.columns)], ignore_index=True)
        
        st.markdown("#### 1. 물동량 현황")
        st.dataframe(v_final_table.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # --- 임시직 투입 상세 테이블 구성 ---
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            tmp_sub = df_temp[df_temp['match_name'] == match_n].copy()
            
            t_rows = []
            for item in ["남", "여", "지게차"]:
                rd = tmp_sub[tmp_sub['구분'] == item]
                # 날짜가 없거나 중간에 데이터가 생기는 경우 모두 대응
                t_vals = [clean_num(rd[col].values[0]) if not rd.empty and col in rd.columns else 0 for col in t_cols]
                t_rows.append([item] + t_vals)
            
            tmp_df = pd.DataFrame(t_rows, columns=['구분'] + t_cols)
            tmp_df.insert(1, '월 합계', tmp_df[t_cols].sum(axis=1))
            
            # 하단 합계 행 추가
            t_total_line = ['일자별 합계', tmp_df['월 합계'].sum()] + tmp_df[t_cols].sum().tolist()
            t_final_table = pd.concat([tmp_df, pd.DataFrame([t_total_line], columns=tmp_df.columns)], ignore_index=True)
            
            st.dataframe(t_final_table.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
