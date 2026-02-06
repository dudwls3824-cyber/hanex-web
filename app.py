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

def clean_num(x):
    if pd.isna(x): return 0
    try:
        s = str(x).replace(',', '').strip()
        nums = re.findall(r'\d+\.?\d*', s)
        return float(nums[0]) if nums else 0
    except: return 0

@st.cache_data(ttl=1)
def fetch_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/14-mE7GtbShJqAHwiuBlZsVFFg8FKuy5tsrcX92ecToY/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(url)
        if '화주사' not in df.columns:
            for i in range(min(len(df), 10)):
                if '화주사' in df.iloc[i].values:
                    df = pd.read_csv(url, header=i+1)
                    break
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['화주사', '구분'])
        # 매칭용 (공백만 제거, 대소문자 유지)
        df['match_name'] = df['화주사'].astype(str).str.replace(' ', '')
        return df
    except: return pd.DataFrame()

# 테마 적용
b64_bg = get_b64(C_IMG)
st.markdown(f"""
<style>
[data-testid='stAppViewContainer'] {{
    background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('data:image/png;base64,{b64_bg}');
    background-size: cover; background-position: center; background-attachment: fixed;
}}
.top-right-logo {{ position: absolute; top: 0px; right: 20px; z-index: 100; }}
.top-right-logo img {{ height: 60px; object-fit: contain; }}
</style>
""", unsafe_allow_html=True)

# 데이터 로드
df_vol = fetch_data('구글 데이터')
df_temp = fetch_data('임시직')

if not df_vol.empty:
    # [중요] 화주사 순서: 시트의 등장 순서 그대로 유지 (dict.fromkeys 사용)
    comps = list(dict.fromkeys(df_vol['화주사'].tolist()))
    
    if 'view' not in st.session_state: st.session_state.view = 'home'

    # 사이드바 구성
    with st.sidebar:
        if os.path.exists(H_LOG): st.image(H_LOG, use_container_width=True)
        
        # 홈 버튼: 세션 상태를 'home'으로 강제 전환
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.view = 'home'
            st.rerun()
            
        st.write("---")
        # 화주사 선택 (순서 유지된 comps 사용)
        selected = st.radio("📍 화주사 목록", comps, index=None if st.session_state.view == 'home' else (comps.index(st.session_state.sel_comp) if 'sel_comp' in st.session_state and st.session_state.sel_comp in comps else None))
        
        if selected:
            st.session_state.view = 'detail'
            st.session_state.sel_comp = selected
            
        mon = st.selectbox("📅 조회 월 선택", [f"{i:02d}" for i in range(1, 13)])
        date_cols = [c for c in df_vol.columns if "2026-" in c]
        t_cols = [c for c in date_cols if c.startswith(f"2026-{mon}")]

    # --- 화면 렌더링 ---
    if st.session_state.view == 'home':
        st.title("📊 남이천1센터 물동량 Dash Board")
        
        res = []
        for c in comps:
            m_name = c.replace(' ', '')
            v_sum = df_vol[df_vol['match_name'] == m_name][t_cols].applymap(clean_num).sum().sum()
            t_sum = 0
            if not df_temp.empty:
                t_sub = df_temp[df_temp['match_name'] == m_name]
                t_cols_act = [col for col in t_cols if col in df_temp.columns]
                t_sum = t_sub[t_cols_act].applymap(clean_num).sum().sum() if t_cols_act else 0
            res.append({"화주사": c, "물동량 합계": v_sum, "임시직 합계": t_sum})
        
        summary_df = pd.DataFrame(res)
        st.metric("📦 센터 전체 물동량 계", f"{int(summary_df['물동량 합계'].sum()):,}")
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(f"#### 📈 화주사별 분석 ({mon}월)")
            st.bar_chart(summary_df.set_index('화주사')['물동량 합계'], color="#002D56")
        with c2:
            st.markdown("#### 📋 현황 요약")
            sdf_disp = summary_df.copy()
            for col in ["물동량 합계", "임시직 합계"]:
                sdf_disp[col] = sdf_disp[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
            st.dataframe(sdf_disp, use_container_width=True, hide_index=True, height=500)

    else:
        # 상세 페이지
        menu = st.session_state.sel_comp
        if menu in L_MAP:
            b64_l = get_b64(os.path.join(L_DIR, L_MAP[menu]))
            if b64_l: st.markdown(f'<div class="top-right-logo"><img src="data:image/png;base64,{b64_l}"></div>', unsafe_allow_html=True)
        
        st.markdown(f"### {menu} 상세 현황 ({mon}월)")
        m_name = menu.replace(' ', '')

        # 1. 물동량 (순서: 구분 -> 월 합계 -> 날짜)
        v_sub = df_vol[df_vol['match_name'] == m_name][['구분'] + t_cols].copy()
        for col in t_cols: v_sub[col] = v_sub[col].apply(clean_num)
        v_g = v_sub.groupby('구분', sort=False).sum().reset_index()
        v_g.insert(1, '월 합계', v_g[t_cols].sum(axis=1))
        v_final = pd.concat([v_g, pd.DataFrame([['일자별 합계', v_g['월 합계'].sum()] + v_g[t_cols].sum().tolist()], columns=v_g.columns)], ignore_index=True)
        
        st.markdown("#### 1. 물동량 현황")
        st.dataframe(v_final.rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

        # 2. 임시직
        st.markdown("---")
        st.markdown("#### 2. 임시직 투입 현황")
        if not df_temp.empty:
            t_sub = df_temp[df_temp['match_name'] == m_name].copy()
            t_cols_act = [col for col in t_cols if col in df_temp.columns]
            
            rows = []
            for itm in ["남", "여", "지게차"]:
                row_data = t_sub[t_sub['구분'] == itm]
                vals = [clean_num(row_data[c].values[0]) if not row_data.empty else 0 for c in t_cols_act]
                rows.append([itm] + vals)
            
            t_df = pd.DataFrame(rows, columns=['구분'] + t_cols_act)
            t_df.insert(1, '월 합계', t_df[t_cols_act].sum(axis=1))
            t_final = pd.concat([t_df, pd.DataFrame([['일자별 합계', t_df['월 합계'].sum()] + t_df[t_cols_act].sum().tolist()], columns=t_df.columns)], ignore_index=True)
            for c in t_cols:
                if c not in t_final.columns: t_final[c] = 0
            
            st.dataframe(t_final[['구분', '월 합계'] + t_cols].rename(columns={c: c.split("-")[-1] for c in t_cols}).style.format(lambda x: f"{int(x):,}" if isinstance(x, (float, int)) and x > 0 else ("-" if isinstance(x, (float, int)) else x)), use_container_width=True, hide_index=True)

st.sidebar.caption("© 2026 HanExpress Nam-Icheon Center")
