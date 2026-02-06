import streamlit as st
import pandas as pd
import urllib.parse, os, base64, re

# 1. 페이지 설정
st.set_page_config(page_title="남이천1센터 물동량 Dash Board", layout="wide")

# 2. 로고 설정
L_DIR = "LOGO"
C_IMG = os.path.join(L_DIR, "센터조감도.png")
H_LOG = os.path.join(L_DIR, "한익스_LOGO.png")
L_MAP = {
    "DKSH L&L":"DKSH L&L_LOGO.png","대호 F&B":"대호 F&B_LOGO.png","덴비코리아":"덴비_LOGO.png",
    "막시무스코리아":"막시무스_LOGO.png","매그니프":"매그니프_LOGO.png","멘소래담":"멘소래담_LOGO.png",
    "머거본":"머거본_LOGO.png","바이오포트코리아":"바이오포트코리아_LOGO.png","시세이도":"시세이도_LOGO.png",
    "유니레버":"유니레버_LOGO.png","커머스파크":"커머스파크_LOGO.png","펄세스":"펄세스_LOGO.png",
    "PRODENTI":"프로덴티_LOGO.png","한국프리오":"한국프리오_LOGO.png","헨켈홈케어":"헨켈홈케어_LOGO.png",
    "네이처리퍼블릭":"네이처리퍼블릭_LOGO.png"
}

def get_b64(p):
    if os.path.exists(p):
        with open(p, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

# 숫자 추출기: "10명", "1,200", "-" 등 모든 케이스 대응
def clean_num(x):
    if pd.isna(x): return 0
    s = str(x).replace(',', '').strip()
    nums = re.findall(r'\d+\.?\d*', s) # 숫자(소수점 포함)만 추출
    return float(nums[0]) if nums else 0

@st.cache_data(ttl=1) # 캐시를 1초로 단축하여 실시간성 확보
def fetch_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(url)
        # 헤더가 밀려있을 경우를 대비해 '화주사' 컬럼이 나올 때까지 위에서부터 탐색
        if '화주사' not in df.columns:
            for i in range(min(len(df), 10)):
                if '화주사' in df.iloc[i].values:
                    df = pd.read_csv(url, header=i+1)
                    break
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['화주사', '구분'])
        # 화주사명 전처리 (비교용)
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '').str.upper()
        return df
    except: return pd.DataFrame()

def apply_theme():
    b64_bg = get_b64(C_IMG)
    st.markdown(f"""
    <style>
    [data-testid='stAppViewContainer'] {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{b64_bg}');
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    @keyframes scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(calc(-150px * 8)); }} }}
    .slider {{ background: white; height: 100px; margin: auto; overflow: hidden; position: relative; width: 100%; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; }}
    .slide-track {{ animation: scroll 25s ease-in-out infinite alternate; display: flex; width: calc(150px * 16); }}
    .slide {{ height: 80px; width: 150px; display: flex; align-items: center; justify-content: center; padding: 10px; }}
    .slide img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
    .top-right-logo {{ position: absolute; top: -10px; right: 0px; height: 80px; width: 200px; display: flex; justify-content: flex-end; align-items: center; z-index: 100; }}
    .top-right-logo img {{ height: 60px; width: auto; object-fit: contain; }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

df_vol = fetch_data('구글 데이터')
df_temp = fetch_data('임시직')

if not df_vol.empty:
    if 'view' not in st.session_state: st.session_state.view = 'home'
    date_cols = [c for c in df_vol.columns if "2026-" in c]
    comps = sorted(list(df_vol['화주사'].unique()))

    with st.sidebar:
        if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
        if st.button("🏠 HOME"): st.session_state.view = 'home'; st.rerun()
        selected = st.radio("📍 화주사 목록", comps, index=None if st.session_state.view == 'home' else (list(comps).index(st.session_state.sel_comp) if 'sel_comp' in st.session_state else 0))
        if selected: st.session_state.view = 'detail'; st.session_state.sel_comp = selected
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        t_cols = [c for c in date_cols if c.startswith(f"2026-{mon}")]

    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        # 로고 슬라이더 (속도 25s)
        slides_html = "".join([f'<div class="slide"><img src="data:image/png;base64,{get_b64(os.path.join(L_DIR, f))}"></div>' for n, f in L_MAP.items() if get_b64(os.path.join(L_DIR, f))])
        st.markdown(f'<div class="slider"><div class="slide-track">{slides_html}</div></div>', unsafe_allow_html=True)

        res = []
        for c in comps:
            m_name = c.replace(' ', '').upper()
            v_sum = df_vol[df_vol['match_name'] == m_name][t_cols].applymap(clean_num).sum().sum()
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                t_cols_act = [col for col in t_cols if col in df_temp.columns]
                t_sum = t_sub[t_cols_act].applymap(clean_num).sum().sum()
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        sdf = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(sdf['물동량 합계'].sum()):,}")
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(f"#### 📈 화주사별 분석 ({mon}월)")
            st.bar_chart(sdf.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            sdf_disp = sdf.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_disp[col] = sdf_disp[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_disp, use_container_width=True, hide_index=True, height=450)

    else:
        # 상세 페이지
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            b64_l = get_b64(os.path.join(L_DIR, L_MAP[menu]))
            if b64_l: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_l}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"## {menu} 상세 현황")
        m_name = menu.replace(' ', '').upper()

        # 1. 물동량
        v_sub = df_vol[df_vol['match_name'] == m_name][['구분'] + t_cols].copy()
        for col in t_cols: v_sub[col] = v_sub[col].apply(clean_num)
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g.insert(1, '월 합계', v_g[t_cols].sum(axis=1))
        v_final = pd.concat([v_g, pd.DataFrame([['일자별 합계', v_g['월 합계'].sum()] + v_g[t_cols].sum().tolist()], columns=['구분', '월 합계']+t_cols)], ignore_index=True)
        
        st.markdown("#### 1. 물동량 현황")
        st.dataframe(v_final.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 2. 임시직
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['match_name'] == m_name].copy()
            t_cols_act = [col for col in t_cols if col in df_temp.columns]
            if not t_sub.empty:
                for col in t_cols_act: t_sub[col] = t_sub[col].apply(clean_num)
                t_g = t_sub.groupby('구분', sort=False).sum().reset_index()
                for itm in ["남", "여", "지게차"]:
                    if itm not in t_g['구분'].values:
                        t_g = pd.concat([t_g, pd.DataFrame([{'구분':itm, **{c:0 for c in t_cols_act}}])], ignore_index=True)
                t_g = t_g[t_g['구분'].isin(["남", "여", "지게차"])].copy()
                t_g['구분'] = pd.Categorical(t_g['구분'], categories=["남", "여", "지게차"], ordered=True)
                t_g = t_g.sort_values('구분')
                t_g.insert(1, '월 합계', t_g[t_cols_act].sum(axis=1))
                t_final = pd.concat([t_g, pd.DataFrame([['일자별 합계', t_g['월 합계'].sum()] + t_g[t_cols_act].sum().tolist()], columns=['구분', '월 합계']+t_cols_act)], ignore_index=True)
                for c in t_cols:
                    if c not in t_final.columns: t_final[c] = 0
                st.dataframe(t_final[['구분', '월 합계'] + t_cols].rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)
            else:
                st.info("해당 화주사 데이터가 없습니다.")

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
