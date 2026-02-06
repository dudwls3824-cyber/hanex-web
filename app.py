import streamlit as st
import pandas as pd
import urllib.parse, os, base64, re

# ==========================================
# 1. 페이지 및 로고 기본 설정
# ==========================================
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")

# 화주사별 로고 매핑 (누락 방지)
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
# 2. 유틸리티 함수 (데이터 처리 및 이미지)
# ==========================================
def get_b64(path):
    """이미지 파일을 base64로 변환 (배경 및 슬라이더용)"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_num(x):
    """지저분한 텍스트에서 숫자만 추출 (중간에 입력된 값도 인식)"""
    if pd.isna(x) or x == "":
        return 0
    s = str(x).replace(',', '').strip()
    # 숫자와 소수점만 추출
    nums = re.findall(r'\d+\.?\d*', s)
    return float(nums[0]) if nums else 0

@st.cache_data(ttl=1)
def fetch_data(sheet_name):
    """구글 시트에서 데이터를 강제로 긁어옴"""
    try:
        gsid = "14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY"
        url = f"https://docs.google.com/spreadsheets/d/{gsid}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        
        # [중요] 모든 열을 문자열(object)로 읽어서 데이터 누락 원천 차단
        df = pd.read_csv(url, dtype=str)
        
        # 헤더 위치 자동 찾기 (화주사 키워드 기준)
        if '화주사' not in df.columns:
            for i in range(min(len(df), 15)):
                if '화주사' in df.iloc[i].values:
                    df = pd.read_csv(url, header=i+1, dtype=str)
                    break
        
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['화주사', '구분'])
        # 매칭용 이름 생성 (공백 제거 및 대문자화)
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '').str.upper()
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# ==========================================
# 3. 화면 스타일 및 애니메이션 설정 (CSS)
# ==========================================
b64_bg = get_b64(C_IMG)
st.markdown(f"""
<style>
    /* 배경 설정 */
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{b64_bg}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    /* 사이드바 홈 로고용 투명 버튼 컨테이너 */
    .logo-container {{ position: relative; width: 100%; text-align: center; margin-bottom: 20px; }}
    .stButton>button {{
        position: absolute !important; top: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important;
        color: transparent !important; z-index: 10 !important; cursor: pointer !important;
    }}
    /* 하단 로고 슬라이더 애니메이션 */
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin-bottom: 25px; overflow: hidden; position: relative; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); display: flex; align-items: center; }}
    .slide-track {{ animation: scroll 25s linear infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide {{ width: 150px; padding: 10px; display: flex; align-items: center; justify-content: center; }}
    .slide img {{ max-height: 80px; width: auto; object-fit: contain; }}
    /* 우상단 화주사 로고 */
    .top-right-logo {{ position: absolute; top: 0px; right: 20px; z-index: 100; }}
    .top-right-logo img {{ height: 65px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 데이터 로드 및 사이드바 구성
# ==========================================
df_vol = fetch_data('구글 데이터')
df_temp = fetch_data('임시직')

if not df_vol.empty:
    # 화주사 순서: 시트의 원본 순서 100% 유지
    comps = list(dict.fromkeys(df_vol['화주사'].tolist()))
    
    if 'view' not in st.session_state:
        st.session_state.view = 'home'

    with st.sidebar:
        # 한익스 로고 위 투명 버튼 (클릭 시 홈 이동)
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if st.button("GO_HOME"):
            st.session_state.view = 'home'
            st.rerun()
        if os.path.exists(H_LOG):
            st.image(H_LOG, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # 화주사 선택 라디오 버튼
        curr_idx = comps.index(st.session_state.sel_comp) if ('sel_comp' in st.session_state and st.session_state.sel_comp in comps) else None
        selected = st.radio("📍 화주사 목록", comps, index=curr_idx if st.session_state.view == 'detail' else None)
        
        if selected:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = selected
            
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        
        # [데이터 누락 방지 로직] 날짜 컬럼 식별
        all_cols = df_vol.columns.tolist()
        # 1~31 숫자 혹은 날짜 형식을 모두 날짜 컬럼으로 간주
        t_cols = [c for c in all_cols if re.search(r'(\d{2,4}[./-]\d{2}[./-]\d{2})|^\d{1,2}$', c)]
        # 선택된 월(mon)에 해당하는 데이터만 필터링
        t_cols = [c for c in t_cols if len(c) <= 2 or f"-{mon}-" in c or c.startswith(f"2026-{mon}")]

    # ==========================================
    # 5. 메인 화면 - [HOME]
    # ==========================================
    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        # 로고 슬라이더 복구
        slides_html = ""
        for n, f in L_MAP.items():
            b64 = get_b64(os.path.join(L_DIR, f))
            if b64:
                slides_html += f'<div class="slide"><img src="data:image/png;base64,{b64}"></div>'
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)
        
        # 데이터 집계
        res = []
        for c in comps:
            m_name = c.replace(' ', '').upper()
            v_rows = df_vol[df_vol['match_name'] == m_name][t_cols]
            v_sum = v_rows.applymap(clean_num).sum().sum()
            
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                t_cols_act = [col for col in t_cols if col in df_temp.columns]
                t_sum = t_sub[t_cols_act].applymap(clean_num).sum().sum() if t_cols_act else 0
            
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        summary_df = pd.DataFrame(res)
        total_v = summary_df['물동량 합계'].sum()
        
        # 📦 센터 전체 물동량 대형 지표 (서식 복구)
        st.markdown(f"""
            <div style="background-color: #002D56; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <h2 style="color: white; margin: 0; font-weight: 400;">📦 {mon}월 센터 전체 물동량 계</h2>
                <h1 style="color: #FFD700; margin: 15px 0; font-size: 4rem; font-weight: 800;">{int(total_v):,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        col_left, col_right = st.columns([1.5, 1])
        with col_left:
            st.markdown("#### 📈 화주사별 물동량 분석")
            st.bar_chart(summary_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with col_right:
            st.markdown("#### 📋 현황 요약")
            disp_df = summary_df.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                disp_df[col] = disp_df[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(disp_df, use_container_width=True, hide_index=True, height=500)

    # ==========================================
    # 6. 메인 화면 - [상세 페이지]
    # ==========================================
    else:
        menu = st.session_state.sel_comp
        # 우상단 화주사 로고 표시
        if menu in L_MAP:
            b64_l = get_b64(os.path.join(L_DIR, L_MAP[menu]))
            if b64_l:
                st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_l}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### {menu} 상세 현황 ({mon}월)")
        m_name = menu.replace(' ', '').upper()

        # --- 1. 물동량 현황 상세 ---
        v_sub = df_vol[df_vol['match_name'] == m_name][['구분'] + t_cols].copy()
        for col in t_cols:
            v_sub[col] = v_sub[col].apply(clean_num)
        
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g.insert(1, '월 합계', v_g[t_cols].sum(axis=1))
        
        # 합계 행 추가
        v_total_row = ['일자별 합계', v_g['월 합계'].sum()] + v_g[t_cols].sum().tolist()
        v_final = pd.concat([v_g, pd.DataFrame([v_total_row], columns=v_g.columns)], ignore_index=True)
        
        st.markdown("#### 1. 물동량 현황")
        st.dataframe(v_final.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # --- 2. 임시직 투입 현황 상세 ---
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['match_name'] == m_name].copy()
            
            rows = []
            for itm in ["남", "여", "지게차"]:
                rd = t_sub[t_sub['구분'] == itm]
                # 날짜 컬럼이 임시직 시트에 없을 경우를 대비해 0으로 채움
                vals = [clean_num(rd[c].values[0]) if not rd.empty and c in rd.columns else 0 for c in t_cols]
                rows.append([itm] + vals)
            
            t_df = pd.DataFrame(rows, columns=['구분'] + t_cols)
            t_df.insert(1, '월 합계', t_df[t_cols].sum(axis=1))
            
            # 합계 행 추가
            t_total_row = ['일자별 합계', t_df['월 합계'].sum()] + t_df[t_cols].sum().tolist()
            t_final = pd.concat([t_df, pd.DataFrame([t_total_row], columns=t_df.columns)], ignore_index=True)
            
            st.dataframe(t_final.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
