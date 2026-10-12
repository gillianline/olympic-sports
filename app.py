import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime

# Set page layout to wide to match typical testing dashboards
st.set_page_config(page_title="Soccer Testing Dashboard", layout="wide")

LOCKED_CONFIG = {"displayModeBar": False}

# ==========================================
# 1. PASSWORD PROTECTION LOGIC
# ==========================================
def check_password():
    """Returns `True` if the user entered the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Remove password from session state for security
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for password.
        st.title("Dashboard Login")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.title("Dashboard Login")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    
    return True # Password correct!

# Stop execution if password fails
if not check_password():
    st.stop()

# ==========================================
# 2. LOAD SECRET DATA
# ==========================================
@st.cache_data(ttl=0)
def load_data():
    df_ff = pd.read_csv(st.secrets["sheet_forceframe"])
    df_roster = pd.read_csv(st.secrets["sheet_roster"])
    df_cmj = pd.read_csv(st.secrets["sheet_cmj"])
    df_bs = pd.read_csv(st.secrets["sheet_belt_squat"])
    df_nb = pd.read_csv(st.secrets["sheet_nordbord"]) 
    
    # Clean up column names: remove hidden spaces and fix capitalization
    for df in [df_ff, df_roster, df_cmj, df_bs, df_nb]:
        df.columns = df.columns.str.strip()
        
        # Bulletproof: Force any variation of "season" or "sport" to be capitalized correctly
        rename_map = {}
        for col in df.columns:
            if col.lower() == 'season': rename_map[col] = 'Season'
            if col.lower() == 'sport': rename_map[col] = 'Sport'
        df.rename(columns=rename_map, inplace=True)
        
        if 'Name' in df.columns:
            df['Name'] = df['Name'].astype(str)
            
    if "Date UTC" in df_nb.columns:
        df_nb = df_nb.rename(columns={"Date UTC": "Date"})
    
    # Smart Merge: Drop overlapping columns from roster before merging 
    def smart_merge(main_df, roster_df):
        cols_to_drop = [c for c in roster_df.columns if c in main_df.columns and c != "Name"]
        clean_roster = roster_df.drop(columns=cols_to_drop)
        return pd.merge(main_df, clean_roster, on="Name", how="left")

    df_ff = smart_merge(df_ff, df_roster)
    df_cmj = smart_merge(df_cmj, df_roster)
    df_bs = smart_merge(df_bs, df_roster)
    df_nb = smart_merge(df_nb, df_roster)
    
    return df_ff, df_cmj, df_bs, df_nb, df_roster

try:
    df_forceframe, df_cmj_full, df_bs_full, df_nb_full, df_roster = load_data()
except Exception as e:
    st.error("Error loading secure data. Please check your sheet links in secrets.toml.")
    st.stop()


# ==========================================
# 3. DASHBOARD UI & SIDEBAR
# ==========================================
st.title("Soccer Testing Dashboard")
st.markdown("---")

# 1. Season Filter (Moved to Main Page)
all_seasons = set()
for df in [df_roster, df_forceframe, df_cmj_full, df_bs_full, df_nb_full]:
    if 'Season' in df.columns:
        all_seasons.update(df['Season'].dropna().astype(str).unique().tolist())

col_season, _ = st.columns([1, 3])
with col_season:
    if all_seasons:
        seasons = list(all_seasons)
        seasons.sort(reverse=True) # Newest at top
        selected_season = st.selectbox("Select Season", ["All Seasons"] + seasons)
    else:
        selected_season = "All Seasons"
        st.warning(" 'Season' column not found in any sheet. Check your Excel headers!")

filtered_roster = df_roster.copy()
if selected_season != "All Seasons" and 'Season' in filtered_roster.columns:
    filtered_roster = filtered_roster[filtered_roster['Season'].astype(str) == selected_season]


# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# 2. Sport Filter
if 'Sport' in filtered_roster.columns:
    sports = filtered_roster['Sport'].dropna().astype(str).unique().tolist()
    selected_sport = st.sidebar.selectbox("Select Sport", ["All Sports"] + sports)
else:
    selected_sport = "All Sports"

if selected_sport != "All Sports":
    filtered_roster = filtered_roster[filtered_roster['Sport'].astype(str) == selected_sport]


# 3. Player Filter
players = filtered_roster['Name'].dropna().astype(str).unique().tolist()
selected_player = st.sidebar.selectbox("Select Player", ["All Players"] + players)


# Filter all raw datasets based on sidebar selections
filtered_ff = df_forceframe.copy()
filtered_cmj = df_cmj_full.copy()
filtered_bs = df_bs_full.copy()
filtered_nb = df_nb_full.copy()

# Apply Season Filter Downstream
if selected_season != "All Seasons":
    if 'Season' in filtered_ff.columns: filtered_ff = filtered_ff[filtered_ff['Season'].astype(str) == selected_season]
    if 'Season' in filtered_cmj.columns: filtered_cmj = filtered_cmj[filtered_cmj['Season'].astype(str) == selected_season]
    if 'Season' in filtered_bs.columns: filtered_bs = filtered_bs[filtered_bs['Season'].astype(str) == selected_season]
    if 'Season' in filtered_nb.columns: filtered_nb = filtered_nb[filtered_nb['Season'].astype(str) == selected_season]

# Apply Sport Filter Downstream
if selected_sport != "All Sports":
    if 'Sport' in filtered_ff.columns: filtered_ff = filtered_ff[filtered_ff['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_cmj.columns: filtered_cmj = filtered_cmj[filtered_cmj['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_bs.columns: filtered_bs = filtered_bs[filtered_bs['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_nb.columns: filtered_nb = filtered_nb[filtered_nb['Sport'].astype(str) == selected_sport]

# Apply Player Filter Downstream
if selected_player != "All Players":
    filtered_ff = filtered_ff[filtered_ff['Name'].astype(str) == selected_player]
    filtered_cmj = filtered_cmj[filtered_cmj['Name'].astype(str) == selected_player]
    filtered_bs = filtered_bs[filtered_bs['Name'].astype(str) == selected_player]
    filtered_nb = filtered_nb[filtered_nb['Name'].astype(str) == selected_player]

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def format_date_clean(date_val):
    if pd.isna(date_val): return "N/A"
    try:
        dt = pd.to_datetime(date_val)
        return dt.strftime("%b %d, %Y")
    except:
        return str(date_val)

def render_vball_table(df):
    """Simple HTML table formatter to match your CSS classes"""
    return df.to_html(classes="table table-striped", index=False, escape=False)


# ==========================================
# 5. DATA PREPARATION FOR HUD
# =========================================

df_forceframe['Date'] = pd.to_datetime(df_forceframe['Date'], errors='coerce')
df_forceframe['Date_Str'] = df_forceframe['Date'].dt.strftime("%m/%d/%y")

ankle_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Ankle', na=False, case=False)]
knee_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Knee', na=False, case=False)]
shoulder_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Shoulder', na=False, case=False)]

hip_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Hip', na=False, case=False)]
hip_ad_ab_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Hip AD/AB', na=False, case=False)]
hip_ir_er_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Hip IR/ER', na=False, case=False)]

nordic_data = pd.DataFrame()

# ---- BELT SQUAT DATA PREP ----
if not filtered_bs.empty and 'Date' in filtered_bs.columns:
    filtered_bs['Date'] = pd.to_datetime(filtered_bs['Date'], errors='coerce')
    filtered_bs['Date_Str'] = filtered_bs['Date'].dt.strftime("%m/%d/%y")
belt_squat_data = filtered_bs.copy()

# ---- CMJ DATA PREP ----
filtered_cmj['Date'] = pd.to_datetime(filtered_cmj['Date'], errors='coerce')
filtered_cmj['Date_Str'] = filtered_cmj['Date'].dt.strftime("%m/%d/%y")
cmj_data = filtered_cmj.copy()

# ---- NORDBORD DATA PREP ----
if not filtered_nb.empty and 'Date' in filtered_nb.columns:
    filtered_nb['Date'] = pd.to_datetime(filtered_nb['Date'], errors='coerce')
    filtered_nb['Date_Str'] = filtered_nb['Date'].dt.strftime("%m/%d/%y")
nordic_data = filtered_nb.copy()

season_label = selected_season if selected_season != "All Seasons" else "All Seasons"
season_key = season_label.replace(" ", "_").lower()
roster_players = filtered_roster['Name'].dropna().unique().tolist()

# ==========================================
# 6. DASHBOARD UI
# ==========================================

testing_tab_intake, testing_tab_cmj, testing_tab_wellness, testing_tab_overall = st.tabs(
    ["Intake Assessment", "CMJ", "Wellness Jump", "Overall Profile"]
)

# ==========================================
# SECTION 5A: INTAKE ASSESSMENT
# ==========================================
with testing_tab_intake:
    st.markdown(
        f"<h3 style='color:#1D1D1F; font-weight:900; text-transform:uppercase;'>Athlete Intake Assessment ({season_label})</h3>",
        unsafe_allow_html=True,
    )
    c_int_ath, _ = st.columns([2, 2])
    with c_int_ath:
        selected_intake_athlete = st.selectbox(
            "Select Athlete for Intake Assessment",
            roster_players,
            key=f"intake_ath_select_{season_key}",
        )

    calf_ath = ankle_data[ankle_data["Name"] == selected_intake_athlete].sort_values("Date") if not ankle_data.empty and "Name" in ankle_data.columns else pd.DataFrame()
    hip_ath = hip_data[hip_data["Name"] == selected_intake_athlete].sort_values("Date") if not hip_data.empty and "Name" in hip_data.columns else pd.DataFrame()
    sh_ath = knee_data[knee_data["Name"] == selected_intake_athlete].sort_values("Date") if not knee_data.empty and "Name" in knee_data.columns else pd.DataFrame()
    nord_ath = nordic_data[nordic_data["Name"] == selected_intake_athlete].sort_values("Date") if not nordic_data.empty and "Name" in nordic_data.columns else pd.DataFrame()
    bs_ath = belt_squat_data[belt_squat_data["Name"] == selected_intake_athlete].sort_values("Date") if not belt_squat_data.empty and "Name" in belt_squat_data.columns else pd.DataFrame()

    has_data = not (calf_ath.empty and hip_ath.empty and sh_ath.empty and nord_ath.empty and bs_ath.empty)

    def render_val_with_arrow(current, initial, fmt="{:.1f}", unit=""):
        if initial == 0 or pd.isna(initial) or pd.isna(current):
            return f"{fmt.format(current) if pd.notna(current) else 0}{unit}"
        diff = current - initial
        pct = (diff / initial) * 100
        arrow = "↑" if diff >= 0 else "↓"
        color = "#28a745" if diff >= 0 else "#dc3545"
        return f"{fmt.format(current)}{unit} <span style='color:{color}; font-size:11px; font-weight:bold;'>({arrow}{abs(pct):.1f}%)</span>"

    def get_peak_and_recent_row(df_sub, l_col, r_col):
        if df_sub.empty or not l_col or not r_col:
            return (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)
        
        df_calc = df_sub.copy()
        df_calc["L_Val"] = pd.to_numeric(df_calc[l_col], errors="coerce").fillna(0.0)
        df_calc["R_Val"] = pd.to_numeric(df_calc[r_col], errors="coerce").fillna(0.0)
        df_calc["Max_Val"] = df_calc[["L_Val", "R_Val"]].max(axis=1)
        
        valid_rows = df_calc[df_calc["Max_Val"] > 0]
        if valid_rows.empty:
            return (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)
        
        peak_row = valid_rows.sort_values("Max_Val", ascending=False).iloc[0]
        max_L, max_R = peak_row["L_Val"], peak_row["R_Val"]
        
        recent_row = valid_rows.sort_values("Date", ascending=True).iloc[-1]
        rec_L, rec_R = recent_row["L_Val"], recent_row["R_Val"]
        
        init_row = valid_rows.sort_values("Date", ascending=True).iloc[0]
        init_L, init_R = init_row["L_Val"], init_row["R_Val"]
        
        return (max_L, max_R), (rec_L, rec_R), (init_L, init_R)

    hud_col1, hud_col2 = st.columns([1.2, 1.8])

    with hud_col1:
        # Dynamic Nodes based on data presence
        node_1_svg = """
        <!-- 1. Belt Squat (Core / Waist) -->
        <line x1="68" y1="84" x2="112" y2="84" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="68" cy="84" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="76" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="88" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
        """ if not bs_ath.empty else ""
        
        node_2_svg = """
        <!-- 2. Hip (AD/AB & IR/ER) -->
        <line x1="58" y1="116" x2="24" y2="116" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="58" cy="116" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="8" y="108" width="16" height="16" rx="4" fill="#4895DB" />
        <text x="16" y="120" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>
        """ if not hip_ath.empty else ""
        
        node_3_svg = """
        <!-- 3. Knee (Ext/Flex) -->
        <line x1="64" y1="140" x2="112" y2="140" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="64" cy="140" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="132" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="144" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>
        """ if not sh_ath.empty else ""
        
        node_4_svg = """
        <!-- 4. Hamstring (NordBord) -->
        <line x1="56" y1="155" x2="24" y2="155" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="56" cy="155" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="8" y="147" width="16" height="16" rx="4" fill="#4895DB" />
        <text x="16" y="159" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>
        """ if not nord_ath.empty else ""
        
        node_5_svg = """
        <!-- 5. Ankle -->
        <line x1="72" y1="178" x2="112" y2="178" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="72" cy="178" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="170" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="182" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
        """ if not calf_ath.empty else ""

        hud_svg_html = f"""
        <div style="background:#FFFFFF; border-radius:16px; padding:16px; border:1px solid #E5E5E7; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
            <div style="color:#1D1D1F; font-weight:800; font-size:13px; letter-spacing:1px; text-transform:uppercase; border-bottom:2px solid #FF8200; padding-bottom:6px; margin-bottom:12px;">ANATOMY LOCATION MAP</div>
            <div style="position:relative; width:100%; height:460px; background:#FAFDFD; border-radius:12px; border:1px solid #D5E5E8; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                <svg viewBox="0 0 160 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
                    <defs>
                        <linearGradient id="anatomicalBodyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#C5CACC" />
                            <stop offset="25%" stop-color="#E8ECEE" />
                            <stop offset="50%" stop-color="#F2F5F7" />
                            <stop offset="75%" stop-color="#D0D5D8" />
                            <stop offset="100%" stop-color="#9AA0A6" />
                        </linearGradient>
                    </defs>
                    <ellipse cx="68" cy="214" rx="20" ry="3.5" fill="#000000" opacity="0.12" />
                    <g stroke="#2C3036" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                        <ellipse cx="68" cy="17" rx="7" ry="9" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 65 25 L 63 33 M 71 25 L 73 33" stroke-width="1.2" />
                        <path d="M 63 33 C 58 33, 48 36, 42 40 C 37 43, 36 50, 39 56 L 43 56 C 47 52, 49 46, 52 44 M 73 33 C 78 33, 88 36, 94 40 C 99 43, 100 50, 97 56 L 93 56 C 89 52, 87 46, 84 44" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 42 40 C 37 43, 35 52, 33 64 C 31 74, 29 82, 27 92 C 25 96, 23 100, 22 104 C 21 106, 23 107, 25 106 C 27 104, 28 98, 30 92 C 33 82, 36 74, 38 64 C 40 54, 42 48, 43 56 Z" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 22 104 C 20 106, 18 108, 17 110 M 23 105 C 21 108, 20 110, 19 112 M 24 105 C 23 108, 22 110, 21 112 M 25 104 C 25 107, 24 109, 23 111" fill="none" stroke-width="0.8" />
                        <path d="M 94 40 C 99 43, 101 52, 103 64 C 105 74, 107 82, 109 92 C 111 96, 113 100, 114 104 C 115 106, 113 107, 111 106 C 109 104, 108 98, 106 92 C 103 82, 100 74, 98 64 C 96 54, 94 48, 93 56 Z" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 114 104 C 116 106, 118 108, 119 110 M 113 105 C 115 108, 116 110, 117 112 M 112 105 C 113 108, 114 110, 115 112 M 111 104 C 111 107, 112 109, 113 111" fill="none" stroke-width="0.8" />
                        <path d="M 52 44 L 54 75 L 52 92 L 68 106 L 84 92 L 82 75 L 84 44 Z" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 52 92 C 50 105, 49 122, 53 138 C 55 144, 55 152, 54 162 C 52 175, 52 192, 54 205 L 48 210 L 58 210 L 59 203 C 60 190, 60 175, 60 162 C 60 152, 60 144, 62 138 C 66 122, 66 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                        <path d="M 84 92 C 86 105, 87 122, 83 138 C 81 144, 81 152, 82 162 C 84 175, 84 192, 82 205 L 88 210 L 78 210 L 77 203 C 76 190, 76 175, 76 162 C 76 152, 76 144, 74 138 C 70 122, 70 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                        <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />
                        <line x1="51" y1="116" x2="85" y2="116" stroke="#D32F2F" stroke-width="1.1" />
                        <line x1="55" y1="168" x2="81" y2="168" stroke="#D32F2F" stroke-width="1.1" />
                    </g>
                    {node_1_svg}
                    {node_2_svg}
                    {node_3_svg}
                    {node_4_svg}
                    {node_5_svg}
                </svg>
            </div>
        </div>
        """
        components.html(hud_svg_html, height=520)

    with hud_col2:
        st.markdown(
            f"""
            <style>
            .hud-details-card {{ background: #FFFFFF; border-radius: 16px; padding: 20px; border: 1px solid #E5E5E7; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }}
            .hud-header-title-light {{ color: #1D1D1F; font-weight: 800; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid #FF8200; padding-bottom: 6px; margin-bottom: 16px; }}
            .hud-metric-row-light {{ background: #F8F9FA; border-left: 4px solid #FF8200; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; color: #1D1D1F; border: 1px solid #E5E5E7; border-left: 4px solid #FF8200; }}
            .hud-metric-row-light-blue {{ background: #F8F9FA; border-left: 4px solid #4895DB; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; color: #1D1D1F; border: 1px solid #E5E5E7; border-left: 4px solid #4895DB; }}
            .node-badge-orange {{ display: inline-block; width: 20px; height: 20px; background: #FF8200; color: #FFFFFF; font-weight: 900; font-size: 11px; border-radius: 4px; text-align: center; line-height: 20px; margin-right: 8px; }}
            .node-badge-blue {{ display: inline-block; width: 20px; height: 20px; background: #4895DB; color: #FFFFFF; font-weight: 900; font-size: 11px; border-radius: 4px; text-align: center; line-height: 20px; margin-right: 8px; }}
            </style>
            <div class="hud-details-card">
                <div class="hud-header-title-light">Location Assessment ({season_label})</div>
            """,
            unsafe_allow_html=True,
        )

        if has_data:
            # 1. BELT SQUAT (Matches Node 1 - Core/Waist)
            if not bs_ath.empty:
                f_c = next((c for c in bs_ath.columns if "peak vertical force" in c.lower() or "force" in c.lower()), None)
                if f_c:
                    bs_ath["PVF_Calc"] = pd.to_numeric(bs_ath[f_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce").fillna(0.0)
                    peak_bs_val = bs_ath["PVF_Calc"].max()
                    rec_bs_val = bs_ath.sort_values("Date").iloc[-1]["PVF_Calc"]
                    date_str = format_date_clean(bs_ath.sort_values("Date").iloc[-1].get("Date"))

                    st.markdown(
                        f"""
                        <div class="hud-metric-row-light">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">1</span>HARNESS BELT SQUAT</span>
                                <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                            </div>
                            <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                <b>Peak Vertical Force:</b> Max {peak_bs_val:.1f}N &nbsp;→&nbsp; <b>Recent:</b> {render_val_with_arrow(rec_bs_val, peak_bs_val, '{:.1f}', 'N')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 2. HIP (Matches Node 2 - Hips)
            if not hip_ath.empty:
                l_col = next((c for c in hip_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                r_col = next((c for c in hip_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                
                dir_col = next((c for c in hip_ath.columns if "direction" in c.lower()), None)
                if not dir_col:
                    dir_col = next((c for c in hip_ath.columns if "test" in c.lower()), None)
                    
                pos_col = next((c for c in hip_ath.columns if "position" in c.lower()), None)

                hip_ad = hip_ath[hip_ath[dir_col].astype(str).str.contains("Adduction", case=False, na=False)] if dir_col else hip_ath
                hip_ab = hip_ath[hip_ath[dir_col].astype(str).str.contains("Abduction", case=False, na=False)] if dir_col else hip_ath

                if pos_col:
                    ad_sup = hip_ad[hip_ad[pos_col].astype(str).str.contains("Supine", case=False, na=False)]
                    ab_sup = hip_ab[hip_ab[pos_col].astype(str).str.contains("Supine", case=False, na=False)]
                    ad_45 = hip_ad[hip_ad[pos_col].astype(str).str.contains("45", case=False, na=False)]
                    ab_45 = hip_ab[hip_ab[pos_col].astype(str).str.contains("45", case=False, na=False)]
                else:
                    ad_sup, ab_sup, ad_45, ab_45 = hip_ad, hip_ab, pd.DataFrame(), pd.DataFrame()

                (ad_sup_maxL, ad_sup_maxR), (ad_sup_recL, ad_sup_recR), _ = get_peak_and_recent_row(ad_sup, l_col, r_col)
                (ab_sup_maxL, ab_sup_maxR), (ab_sup_recL, ab_sup_recR), _ = get_peak_and_recent_row(ab_sup, l_col, r_col)
                (ad_45_maxL, ad_45_maxR), (ad_45_recL, ad_45_recR), _ = get_peak_and_recent_row(ad_45, l_col, r_col)
                (ab_45_maxL, ab_45_maxR), (ab_45_recL, ab_45_recR), _ = get_peak_and_recent_row(ab_45, l_col, r_col)
                
                date_str = format_date_clean(hip_ath.sort_values("Date").iloc[-1].get("Date")) if not hip_ath.empty else "N/A"

                supine_html = ""
                if not ad_sup.empty or not ab_sup.empty:
                    supine_html = f"<b>Adduction (Supine Knee):</b> Max L {ad_sup_maxL:.1f}N | R {ad_sup_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ad_sup_recL, ad_sup_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ad_sup_recR, ad_sup_maxR, '{:.1f}', 'N')}<br><b>Abduction (Supine Knee):</b> Max L {ab_sup_maxL:.1f}N | R {ab_sup_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ab_sup_recL, ab_sup_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ab_sup_recR, ab_sup_maxR, '{:.1f}', 'N')}"
                
                forty_five_html = ""
                if not ad_45.empty or not ab_45.empty:
                    divider = '<div style="margin-top:6px; margin-bottom:6px; border-bottom:1px solid #D5E5E8;"></div>' if supine_html else ''
                    forty_five_html = f"{divider}<b>Adduction (45°):</b> Max L {ad_45_maxL:.1f}N | R {ad_45_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ad_45_recL, ad_45_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ad_45_recR, ad_45_maxR, '{:.1f}', 'N')}<br><b>Abduction (45°):</b> Max L {ab_45_maxL:.1f}N | R {ab_45_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ab_45_recL, ab_45_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ab_45_recR, ab_45_maxR, '{:.1f}', 'N')}"

                st.markdown(
                    f"""<div class="hud-metric-row-light-blue">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
<span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">2</span>HIP ADDUCTION & ABDUCTION</span>
<span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
</div>
<div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
{supine_html}{forty_five_html}
</div>
</div>""",
                    unsafe_allow_html=True,
                )
                
            # 3. KNEE (Matches Node 3 - Knees)
            if not sh_ath.empty:
                l_col = next((c for c in sh_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                r_col = next((c for c in sh_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                dir_c = next((c for c in sh_ath.columns if "direction" in c.lower() or "test" in c.lower()), None)
                knee_ext = sh_ath[sh_ath[dir_c].astype(str).str.contains("Extension", case=False, na=False)] if dir_c else sh_ath
                knee_flx = sh_ath[sh_ath[dir_c].astype(str).str.contains("Flexion", case=False, na=False)] if dir_c else sh_ath

                (ke_maxL, ke_maxR), (ke_recL, ke_recR), (_, _) = get_peak_and_recent_row(knee_ext, l_col, r_col)
                (kf_maxL, kf_maxR), (kf_recL, kf_recR), (_, _) = get_peak_and_recent_row(knee_flx, l_col, r_col)
                latest_date_str = format_date_clean(knee_ext.sort_values("Date").iloc[-1].get("Date")) if not knee_ext.empty else "N/A"

                st.markdown(
                    f"""
                    <div class="hud-metric-row-light">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">3</span>KNEE EXTENSION & FLEXION</span>
                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {latest_date_str}</span>
                        </div>
                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                            <b>Extension:</b> Max L {ke_maxL:.1f}N | R {ke_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ke_recL, ke_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ke_recR, ke_maxR, '{:.1f}', 'N')}<br>
                            <b>Flexion:</b> Max L {kf_maxL:.1f}N | R {kf_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(kf_recL, kf_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(kf_recR, kf_maxR, '{:.1f}', 'N')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # 4. NORDBORD HAMSTRING (Matches Node 4 - Back of Thigh)
            if not nord_ath.empty:
                l_col = next((c for c in nord_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                r_col = next((c for c in nord_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                (nord_maxL, nord_maxR), (nord_recL, nord_recR), (_, _) = get_peak_and_recent_row(nord_ath, l_col, r_col)
                date_str = format_date_clean(nord_ath.sort_values("Date").iloc[-1].get("Date")) if not nord_ath.empty else "N/A"

                st.markdown(
                    f"""
                    <div class="hud-metric-row-light-blue">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">4</span>NORDBORD HAMSTRING</span>
                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                        </div>
                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                            <b>Peak Force:</b> L {nord_maxL:.1f}N | R {nord_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(nord_recL, nord_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(nord_recR, nord_maxR, '{:.1f}', 'N')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # 5. ANKLE (Matches Node 5 - Lower Calf/Ankle)
            if not calf_ath.empty:
                l_col = next((c for c in calf_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                r_col = next((c for c in calf_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                (ank_maxL, ank_maxR), (ank_recL, ank_recR), (_, _) = get_peak_and_recent_row(calf_ath, l_col, r_col)
                date_str = format_date_clean(calf_ath.sort_values("Date").iloc[-1].get("Date")) if not calf_ath.empty else "N/A"

                st.markdown(
                    f"""
                    <div class="hud-metric-row-light">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">5</span>ANKLE PLANTAR FLEXION</span>
                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                        </div>
                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                            <b>Max Force:</b> L {ank_maxL:.1f}N | R {ank_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ank_recL, ank_maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(ank_recR, ank_maxR, '{:.1f}', 'N')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.info(f"No Intake Assessment records found for {selected_intake_athlete} in {season_label}.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    if has_data:
        st.markdown(f"### Intake Assessment Raw Logs for {selected_intake_athlete} ({season_label})")

        def render_clean_log(df_sub, log_name):
            df_display = df_sub.copy()
            def get_movement(row):
                pos = row.get('Position')
                dir_ = row.get('Direction')
                test = row.get('Test')
                has_pos = pd.notna(pos) and str(pos).strip() != ""
                has_dir = pd.notna(dir_) and str(dir_).strip() != ""
                if has_pos and has_dir: return f"{pos} - {dir_}"
                elif has_pos: return pos
                elif has_dir: return f"{test} - {dir_}"
                else: return test

            df_display['Position'] = df_display.apply(get_movement, axis=1)

            target_cols = [
                "Date", "Position", "L Max Force (N)", "R Max Force (N)", 
                "Max Imbalance", "L Max Ratio", "R Max Ratio"
            ]
            final_cols = [c for c in target_cols if c in df_display.columns]
            df_final = df_display[final_cols].copy()
            df_final = df_final.replace(["N/A", "NaN", "nan", ""], pd.NA)
            df_final = df_final.dropna(axis=1, how='all').fillna("")
            st.markdown(render_vball_table(df_final), unsafe_allow_html=True)

        if not calf_ath.empty:
            with st.expander("Ankle Plantar Flexion Log", expanded=False):
                render_clean_log(calf_ath, "Ankle Assessment")

        if not sh_ath.empty:
            with st.expander("Knee Extension / Flexion Log", expanded=False):
                render_clean_log(sh_ath, "Knee Assessment")

        hip_ad_ath = hip_ad_ab_data[hip_ad_ab_data["Name"] == selected_intake_athlete].sort_values("Date") if not hip_ad_ab_data.empty else pd.DataFrame()
        if not hip_ad_ath.empty:
            with st.expander("Hip AD/AB Log", expanded=False):
                render_clean_log(hip_ad_ath, "Hip AD/AB")

        hip_ir_ath = hip_ir_er_data[hip_ir_er_data["Name"] == selected_intake_athlete].sort_values("Date") if not hip_ir_er_data.empty else pd.DataFrame()
        if not hip_ir_ath.empty:
            with st.expander("Hip IR/ER Log", expanded=False):
                render_clean_log(hip_ir_ath, "Hip IR/ER")
            
        shoulder_ath = shoulder_data[shoulder_data["Name"] == selected_intake_athlete].sort_values("Date") if not shoulder_data.empty else pd.DataFrame()
        if not shoulder_ath.empty:
            with st.expander("Shoulder Log", expanded=False):
                render_clean_log(shoulder_ath, "Shoulder")

        if not bs_ath.empty:
            with st.expander("Isometric Belt Squat Log", expanded=False):
                target_cols_bs = [
                    "Test Type", "Date", "BW [KG]", "Peak Vertical Force [N]", 
                    "Peak Vertical Force / BM [N/kg]", "RFD - 100ms [N/s]", 
                    "Force at 100ms [N]", "Start Time to 80% Net Peak Force [s]"
                ]
                final_cols_bs = [c for c in target_cols_bs if c in bs_ath.columns]
                df_bs_display = bs_ath[final_cols_bs].copy()
                if "Date" in df_bs_display.columns:
                    df_bs_display["Date"] = pd.to_datetime(df_bs_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")
                for col in df_bs_display.columns:
                    if col not in ["Test Type", "Date"]:
                        df_bs_display[col] = pd.to_numeric(df_bs_display[col], errors="coerce").apply(
                            lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA
                        )
                df_bs_display = df_bs_display.dropna(axis=1, how='all').fillna("-")
                st.dataframe(df_bs_display, use_container_width=True, hide_index=True)

        if not nord_ath.empty:
            with st.expander("NordBord Hamstring Log", expanded=False):
                target_cols_nb = [
                    "Test", "Date", "L Max Force (N)", "R Max Force (N)", 
                    "Max Imbalance (%)", "L Max Torque (Nm)", "R Max Torque (Nm)"
                ]
                final_cols_nb = [c for c in target_cols_nb if c in nord_ath.columns]
                df_nb_display = nord_ath[final_cols_nb].copy()
                if "Date" in df_nb_display.columns:
                    df_nb_display["Date"] = pd.to_datetime(df_nb_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")
                for col in df_nb_display.columns:
                    if col not in ["Test", "Date"]:
                        df_nb_display[col] = pd.to_numeric(df_nb_display[col], errors="coerce").apply(
                            lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA
                        )
                df_nb_display = df_nb_display.dropna(axis=1, how='all').fillna("-")
                st.dataframe(df_nb_display, use_container_width=True, hide_index=True)


# ==========================================
# SECTION 5B: CMJ TAB
# ==========================================
with testing_tab_cmj:
    st.markdown(
        f'<div class="vball-section-title">CMJ Performance History — {season_label}</div>',
        unsafe_allow_html=True,
    )

    c_filter, _ = st.columns([1, 2])
    with c_filter:
        selected_player_t = st.selectbox(
            "Select Athlete:", roster_players, key=f"cmj_player_select_{season_key}"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    p_cmj = (
        cmj_data[cmj_data["Name"] == selected_player_t]
        .sort_values("Date")
        .copy()
        if not cmj_data.empty
        else pd.DataFrame()
    )

    jump_cols = [c for c in p_cmj.columns if "jump" in c.lower() or "height" in c.lower()]
    j_col = jump_cols[0] if jump_cols else None
    rsi_cols = [c for c in p_cmj.columns if "rsi" in c.lower()]
    rsi_col = rsi_cols[0] if rsi_cols else None

    if not p_cmj.empty and j_col:
        p_cmj["Jump_Height_Clean"] = pd.to_numeric(
            p_cmj[j_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
            errors="coerce",
        )

        fig_jump_trend = go.Figure()
        fig_jump_trend.add_trace(
            go.Scatter(
                x=p_cmj["Date"],
                y=p_cmj["Jump_Height_Clean"],
                name="Jump Height",
                mode="lines+markers",
                connectgaps=True,
                yaxis="y",
                line=dict(color="#FF8200", width=4),
                marker=dict(size=8, color="#FF8200"),
            )
        )

        if rsi_col:
            p_cmj["RSI_Clean"] = pd.to_numeric(
                p_cmj[rsi_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                errors="coerce",
            )
            fig_jump_trend.add_trace(
                go.Scatter(
                    x=p_cmj["Date"],
                    y=p_cmj["RSI_Clean"],
                    name="RSI Modified",
                    mode="lines+markers",
                    connectgaps=True,
                    yaxis="y2",
                    line=dict(color="#38BDF8", width=3, dash="dot"),
                    marker=dict(size=8, color="#38BDF8"),
                )
            )

        fig_jump_trend.update_layout(
            height=320,
            margin=dict(l=40, r=40, t=50, b=40),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.08,
                xanchor="left",
                x=0.01,
                font=dict(size=13, color="#0F172A"),
            ),
            xaxis=dict(
                title=None,
                type="date",
                tickformat="%b %d\n%Y",
                showgrid=False,
                showline=True,
                linewidth=1.5,
                linecolor="#0F172A",
                tickfont=dict(color="#64748B", size=12),
            ),
            yaxis=dict(
                showgrid=False,
                showline=True,
                linewidth=1.5,
                linecolor="#0F172A",
                tickfont=dict(color="#64748B", size=12),
                side="left",
            ),
            yaxis2=dict(
                showgrid=False,
                showline=True,
                linewidth=1.5,
                linecolor="#0F172A",
                tickfont=dict(color="#64748B", size=12),
                overlaying="y",
                side="right",
                anchor="x",
            ),
        )
        st.plotly_chart(fig_jump_trend, use_container_width=True, key=f"cmj_trend_{season_key}")

        st.divider()

        st.markdown(f"### Jump History Logs for {selected_player_t} ({season_label})")
        
        jh_col = next((c for c in p_cmj.columns if "jump height" in c.lower()), None)
        rsi_col = next((c for c in p_cmj.columns if "rsi" in c.lower()), None)
        
        target_cols = ["Test Type", "Date", "BW [KG]"]
        if jh_col: target_cols.append(jh_col)
        target_cols.extend(["Peak Power [W]", "Eccentric Braking RFD [N/s]"])
        if rsi_col: target_cols.append(rsi_col)
        target_cols.extend(["Concentric Peak Velocity [m/s]", "CMJ Stiffness [N/m]"])
        
        final_cols = [c for c in target_cols if c in p_cmj.columns]
        df_cmj_display = p_cmj[final_cols].copy()
        
        rename_map = {}
        if jh_col: rename_map[jh_col] = "Jump Height (cm)"
        if rsi_col: rename_map[rsi_col] = "RSI [m/s]"
        df_cmj_display = df_cmj_display.rename(columns=rename_map)
        
        if "Date" in df_cmj_display.columns:
            df_cmj_display["Date"] = pd.to_datetime(df_cmj_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")

        for col in df_cmj_display.columns:
            if col not in ["Test Type", "Date"]:
                df_cmj_display[col] = pd.to_numeric(df_cmj_display[col], errors="coerce").apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA
                )
        
        df_cmj_display = df_cmj_display.dropna(axis=1, how='all').fillna("-")
        
        st.dataframe(df_cmj_display, use_container_width=True, hide_index=True)
        
    else:
        st.info(f"No Countermovement Jump (CMJ) logs found for {selected_player_t} in {season_label}.")       


# ==========================================
# SECTION 5C: WELLNESS JUMP TAB
# ==========================================
with testing_tab_wellness:
    st.markdown(
        f'<div class="vball-section-title">Neuromuscular Readiness & Wellness ({season_label})</div>',
        unsafe_allow_html=True,
    )
    
    # Helpers for the Wellness Score
    def calc_wellness_for_date(ath_cmj_df, target_date_str):
        df_s = ath_cmj_df.sort_values("Date")
        j_c = next((c for c in df_s.columns if "jump" in c.lower() or "height" in c.lower()), None)
        r_c = next((c for c in df_s.columns if "rsi" in c.lower()), None)
        
        if not j_c: return 0
        df_s["JH_Clean"] = pd.to_numeric(df_s[j_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
        if r_c: df_s["RSI_Clean"] = pd.to_numeric(df_s[r_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
        
        valid_j = df_s.dropna(subset=["JH_Clean"])
        if valid_j.empty: return 0
        
        max_j = valid_j["JH_Clean"].max()
        target_df = valid_j[valid_j["Date_Str"] == target_date_str]
        if target_df.empty: return 0
        
        latest_j = target_df.iloc[-1]["JH_Clean"]
        j_score = (latest_j / max_j * 100) if max_j > 0 else 0
        
        if r_c:
            valid_r = df_s.dropna(subset=["RSI_Clean"])
            if not valid_r.empty:
                max_r = valid_r["RSI_Clean"].max()
                target_r = valid_r[valid_r["Date_Str"] == target_date_str]
                if not target_r.empty:
                    latest_r = target_r.iloc[-1]["RSI_Clean"]
                    r_score = (latest_r / max_r * 100) if max_r > 0 else 0
                    if r_score > 0:
                        return (j_score + r_score) / 2
        return j_score

    def get_readiness_color(val):
        if val >= 90: return "#28a745" # Green
        elif val >= 80: return "#ffc107" # Yellow
        else: return "#dc3545" # Red
        
    def create_wellness_gauge(score, height=230):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={'suffix': "%", 'font': {'size': 30, 'color': '#1D1D1F'}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#1D1D1F"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 80], 'color': "rgba(220, 53, 69, 0.6)"},   
                    {'range': [80, 90], 'color': "rgba(255, 193, 7, 0.6)"},  
                    {'range': [90, 100], 'color': "rgba(40, 167, 69, 0.6)"}  
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10))
        return fig

    sel_cmj_mode = st.radio("Select View Mode", ["Individual Athlete", "Team CMJ Summary"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # --- 1. INDIVIDUAL ATHLETE PROFILE ---------------------------------------
    # -------------------------------------------------------------------------
    if sel_cmj_mode == "Individual Athlete":
        c_cmj_ath, c_cmj_date = st.columns([2, 2])
        with c_cmj_ath:
            sel_cmj_ath = st.selectbox(
                "Select Athlete",
                roster_players,
                key="cmj_dash_ath_sel",
            )
        
        ath_cmj_all = cmj_data[cmj_data["Name"] == sel_cmj_ath].sort_values("Date")

        if ath_cmj_all.empty:
            st.info(f"No CMJ records found for {sel_cmj_ath}.")
        else:
            valid_dates = (
                ath_cmj_all["Date"]
                .dropna()
                .drop_duplicates()
                .sort_values(ascending=False)
                .dt.strftime("%m/%d/%y")
                .tolist()
            )
            
            with c_cmj_date:
                sel_test_date_str = st.selectbox(
                    "Test Date",
                    valid_dates,
                    index=0,
                    key="cmj_dash_date_sel",
                )

            cur_idx_list = ath_cmj_all[
                ath_cmj_all["Date"].dt.strftime("%m/%d/%y") == sel_test_date_str
            ].index.tolist()
            
            cur_test_row = ath_cmj_all.loc[cur_idx_list[-1]]
            base_test_row = ath_cmj_all.iloc[0]
            
            cmj_col = next((c for c in cmj_data.columns if "jump height" in c.lower() or "height" in c.lower()), "Jump Height")

            meta_lookup = filtered_roster[filtered_roster["Name"] == sel_cmj_ath]
            photo_val = meta_lookup["Picture"].iloc[0] if not meta_lookup.empty and "Picture" in meta_lookup.columns else "https://www.w3schools.com/howto/img_avatar.png"
            pos_val = meta_lookup["Position"].iloc[0] if not meta_lookup.empty and "Position" in meta_lookup.columns else "N/A"

            cmj_metric_defs = [
                {
                    "label": "Jump Height",
                    "col": cmj_col,
                    "fmt": "{:.1f}",
                },
                {
                    "label": "Jump Momentum",
                    "col": "Jump Momentum",
                    "alt_col": "Take-off Momentum [kg m/s]",
                    "fmt": "{:.1f}",
                },
                {
                    "label": "Peak Velocity",
                    "col": "Concentric Peak Velocity [m/s]",
                    "fmt": "{:.2f}",
                },
                {
                    "label": "Mean Con Force",
                    "col": "Relative Mean Con Force",
                    "alt_col": "Concentric Mean Force [N]",
                    "fmt": "{:.0f}",
                },
                {
                    "label": "Force @ 0 Velocity",
                    "col": "Relative Force @ 0 Velo",
                    "alt_col": "Force at Zero Velocity [N]",
                    "fmt": "{:.0f}",
                },
                {
                    "label": "Positive Impulse",
                    "col": "Positive Impulse [N s]",
                    "fmt": "{:.1f}",
                },
                {
                    "label": "P1 Con Impulse",
                    "col": "P1 Concentric Impulse [N s]",
                    "fmt": "{:.1f}",
                },
                {
                    "label": "P2 Con Impulse",
                    "col": "P2 Concentric Impulse [N s]",
                    "fmt": "{:.1f}",
                },
                {
                    "label": "P2:P1 Impulse Ratio",
                    "col": "P2 Concentric Impulse:P1 Concentric Impulse",
                    "fmt": "{:.2f}",
                },
            ]

            display_score = int(round(calc_wellness_for_date(ath_cmj_all, sel_test_date_str)))

            top_col1, top_col2, top_col3 = st.columns([1.2, 2.2, 1.6])
            
            with top_col1:
                ath_card_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:18px; text-align:center; padding:8px 10px; border-radius:6px 6px 0 0;">{sel_cmj_ath}</div><div style="border:1px solid #E2E8F0; border-top:none; border-radius:0 0 6px 6px; padding:16px; background:white; display:flex; align-items:center; gap:16px;"><img src="{photo_val}" style="width:95px; height:95px; border-radius:8px; object-fit:contain; border:2px solid #FF8200;"><div style="font-size:14px; line-height:1.8; color:#1D1D1F;"><b>Position:</b> {pos_val}</div></div>"""
                st.markdown(ath_card_html, unsafe_allow_html=True)
                comp_factor = st.selectbox(
                    "Comparison Factor",
                    ["Individual", "Team", "Position"],
                    key="cmj_dash_comp_sel",
                )

            with top_col2:
                table_rows_str = ""
                for m_info in cmj_metric_defs:
                    lbl = m_info["label"]
                    col_name = m_info["col"] if m_info["col"] in cur_test_row else m_info.get("alt_col", m_info["col"])
                    fmt = m_info["fmt"]
                    
                    c_val = float(cur_test_row.get(col_name, 0.0)) if col_name in cur_test_row and pd.notna(cur_test_row.get(col_name)) else 0.0
                    b_val = float(base_test_row.get(col_name, 0.0)) if col_name in base_test_row and pd.notna(base_test_row.get(col_name)) else 0.0
                    
                    diff = ((c_val - b_val) / b_val * 100) if b_val > 0 else 0.0
                    pct_color = "#137333" if diff >= 0 else "#D93025"
                    
                    table_rows_str += f"""<tr><td style="text-align:left !important; padding-left:12px; font-weight:600;">{lbl}</td><td style="color:#64748B;">{fmt.format(b_val)}</td><td style="font-weight:800; background:#F0F7FF; border: 1px solid #3B82F6;">{fmt.format(c_val)}</td><td style="font-weight:800; color:{pct_color};">{diff:+.0f}%</td></tr>"""

                full_table_html = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Countermovement Jump Performance</div><table class="scout-table" style="width:100%; border:1px solid #E2E8F0; border-top:none; background:white; border-collapse:collapse; margin-bottom:0;"><thead><tr style="background:#F8FAFC; color:#64748B; font-size:11px;"><th style="text-align:left !important; padding:6px 12px;">Metric</th><th style="padding:6px;">Baseline (Overall)</th><th style="padding:6px; background:#EBF5FF; color:#1E40AF;">Current</th><th style="padding:6px;">% Change</th></tr></thead><tbody>{table_rows_str}</tbody></table>"""
                st.markdown(full_table_html, unsafe_allow_html=True)

            with top_col3:
                gauge_header = f"""<div style="background:#4895DB; color:white; font-weight:900; font-size:14px; text-align:center; padding:6px; border-radius:6px 6px 0 0;">Wellness Score<br><span style="font-size:11px; font-weight:600;">{sel_test_date_str}</span></div>"""
                st.markdown(gauge_header, unsafe_allow_html=True)
                fig_gauge = create_wellness_gauge(display_score, height=230)
                st.plotly_chart(
                    fig_gauge,
                    use_container_width=True,
                    config=LOCKED_CONFIG,
                    key="cmj_wellness_gauge_ind",
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<div class="section-header">Countermovement Jump Performance Standards </div>',
                unsafe_allow_html=True,
            )
            
            chart_col, legend_col = st.columns([4.2, 1.1])

            with chart_col:
                bar_metrics_excel = [
                    {"name": "Jump Height", "col": cmj_col, "invert": False},
                    {"name": "Jump Momentum", "col": "Jump Momentum", "alt_col": "Take-off Momentum [kg m/s]", "invert": False},
                    {"name": "Peak Velocity", "col": "Concentric Peak Velocity [m/s]", "invert": False},
                    {"name": "Mean Con Force", "col": "Relative Mean Con Force", "alt_col": "Concentric Mean Force [N]", "invert": False},
                    {"name": "Force @ 0 Velocity", "col": "Relative Force @ 0 Velo", "alt_col": "Force at Zero Velocity [N]", "invert": False},
                    {"name": "Positive Impulse", "col": "Positive Impulse [N s]", "invert": False},
                    {"name": "P1 Con Impulse", "col": "P1 Concentric Impulse [N s]", "invert": False},
                    {"name": "P2 Con Impulse", "col": "P2 Concentric Impulse [N s]", "invert": False},
                    {"name": "CM Depth", "col": "Adjusted CMD", "alt_col": "Countermovement Depth [cm]", "invert": False},
                    {"name": "Time to Takeoff", "col": "Contraction Time [ms]", "alt_col": "Time to Takeoff [s]", "invert": True},
                ]

                if comp_factor == "Individual":
                    ref_pool_df = cmj_data[cmj_data["Name"] == sel_cmj_ath]
                    title_prefix = "Individual"
                elif comp_factor == "Position":
                    pos_athletes = filtered_roster[filtered_roster["Position"] == pos_val]["Name"].unique() if "Position" in filtered_roster.columns else []
                    ref_pool_df = cmj_data[cmj_data["Name"].isin(pos_athletes)]
                    if ref_pool_df.empty:
                        ref_pool_df = cmj_data
                    title_prefix = "Position"
                else:
                    ref_pool_df = cmj_data
                    title_prefix = "Team"

                t_scores = []
                x_labels = []
                for bm in bar_metrics_excel:
                    x_labels.append(bm["name"])
                    cname = bm["col"] if bm["col"] in cur_test_row else bm.get("alt_col", bm["col"])
                    
                    ath_v = abs(float(cur_test_row.get(cname, 0.0))) if cname in cur_test_row and pd.notna(cur_test_row.get(cname)) else 0.0
                    
                    if cname in ref_pool_df.columns and len(ref_pool_df[cname].dropna()) > 1:
                        valid_series = pd.to_numeric(ref_pool_df[cname], errors='coerce').dropna().abs()
                        m_mean = valid_series.mean()
                        m_std = valid_series.std(ddof=1)
                        if m_std > 0:
                            z_val = -1.0 * ((ath_v - m_mean) / m_std) if bm["invert"] else (ath_v - m_mean) / m_std
                            t_val = 50.0 + (z_val * 10.0)
                            t_scores.append(round(min(100.0, max(0.0, t_val)), 1))
                        else:
                            t_scores.append(50.0)
                    else:
                        t_scores.append(50.0)

                fig_bands = go.Figure()
                bands = [
                    {"y0": 0, "y1": 20, "color": "#A00000"},
                    {"y0": 20, "y1": 30, "color": "#E60000"},
                    {"y0": 30, "y1": 40, "color": "#F05656"},
                    {"y0": 40, "y1": 45, "color": "#F8A2A2"},
                    {"y0": 45, "y1": 55, "color": "#FFFFFF"},
                    {"y0": 55, "y1": 60, "color": "#C3E8A8"},
                    {"y0": 60, "y1": 70, "color": "#81D350"},
                    {"y0": 70, "y1": 80, "color": "#33A338"},
                    {"y0": 80, "y1": 100, "color": "#1C7426"},
                ]
                for b in bands:
                    fig_bands.add_hrect(
                        y0=b["y0"], y1=b["y1"], fillcolor=b["color"],
                        line_width=0, opacity=1.0, layer="below",
                    )
                
                fig_bands.add_trace(
                    go.Bar(
                        x=x_labels,
                        y=t_scores,
                        marker=dict(
                            color="#3A3D40",
                            line=dict(color="#1A1C1E", width=1.5),
                        ),
                        width=0.42,
                        text=[f"<b>{val:.1f}</b>" for val in t_scores],
                        textposition="inside",
                        insidetextanchor="middle",
                        textfont=dict(color="white", size=12),
                        cliponaxis=False,
                    )
                )

                category_boxes = [
                    {"x0": 0.55, "x1": 2.45, "text": "Speed", "bg": "#F8E2E2"},
                    {"x0": 2.55, "x1": 6.45, "text": "Strength", "bg": "#EBF3DF"},
                    {"x0": 6.55, "x1": 7.45, "text": "Power", "bg": "#D3E2F4"},
                    {"x0": 7.55, "x1": 9.45, "text": "Jump Strategy", "bg": "#E6E1F2"},
                ]
                
                for cb in category_boxes:
                    fig_bands.add_shape(
                        type="rect", xref="x", yref="paper",
                        x0=cb["x0"], x1=cb["x1"], y0=-0.16, y1=-0.08,
                        fillcolor=cb["bg"], line=dict(width=0), layer="above",
                    )
                    fig_bands.add_annotation(
                        xref="x", yref="paper",
                        x=(cb["x0"] + cb["x1"]) / 2, y=-0.12,
                        text=f"<b>{cb['text']}</b>", showarrow=False,
                        font=dict(size=11, color="#111827"), align="center",
                    )

                fig_bands.update_layout(
                    height=450,
                    margin=dict(l=30, r=10, t=15, b=65),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(
                        tickangle=0,
                        tickfont=dict(size=10.5, weight="bold", color="#111827"),
                        showgrid=False, showline=True, linecolor="#6B7280",
                    ),
                    yaxis=dict(
                        range=[0, 100], dtick=10,
                        showgrid=False, showline=True, linecolor="#6B7280",
                        title=dict(
                            text=f"{title_prefix} T-Score Performance Rating",
                            font=dict(size=12, weight="bold", color="#4B5563"),
                        ),
                    ),
                    showlegend=False,
                )
                
                st.plotly_chart(
                    fig_bands,
                    use_container_width=True,
                    config=LOCKED_CONFIG,
                    key=f"cmj_standards_chart_{comp_factor}",
                )

            with legend_col:
                legend_table_html = """<div style="background:#4895DB; color:white; font-weight:800; font-size:12px; text-align:center; padding:6px; border-radius:4px 4px 0 0;">Performance Bands<br><span style="font-size:10px; font-weight:600;">T-Score Rating</span></div><table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-weight:700;"><tr style="background:#1C7426; color:white;"><td style="padding:4px;">Excellent</td><td>> 80</td></tr><tr style="background:#33A338; color:white;"><td style="padding:4px;">Very Good</td><td>70 - 80</td></tr><tr style="background:#81D350; color:#111827;"><td style="padding:4px;">Good</td><td>60 - 70</td></tr><tr style="background:#C3E8A8; color:#111827;"><td style="padding:4px;">Above Avg.</td><td>55 - 60</td></tr><tr style="background:#FFFFFF; color:#111827; border-top:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;"><td style="padding:4px;">Average</td><td>45 - 55</td></tr><tr style="background:#F8A2A2; color:#111827;"><td style="padding:4px;">Below Avg.</td><td>40 - 45</td></tr><tr style="background:#F05656; color:white;"><td style="padding:4px;">Poor</td><td>30 - 40</td></tr><tr style="background:#E60000; color:white;"><td style="padding:4px;">Very Poor</td><td>20 - 30</td></tr><tr style="background:#A00000; color:white;"><td style="padding:4px;">Extremely Poor</td><td>< 20</td></tr></table>"""
                st.markdown(legend_table_html, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # --- 2. TEAM CMJ SUMMARY -------------------------------------------------
    # -------------------------------------------------------------------------
    elif sel_cmj_mode == "Team CMJ Summary":
        st.markdown("### Team Wellness Score Overview")
        if cmj_data.empty:
            st.info("No CMJ data available.")
        else:
            team_cmj_dates = cmj_data["Date"].dropna().dt.strftime("%m/%d/%y").drop_duplicates().sort_values(ascending=False).tolist()

            c_sum_d1, c_sum_d2 = st.columns([1.5, 2])
            with c_sum_d1:
                sel_team_cmj_date = st.selectbox("Evaluation Test Date", team_cmj_dates, index=0, key="team_cmj_eval_date")
            with c_sum_d2:
                positions = [p for p in filtered_roster["Position"].unique() if pd.notna(p) and p != "N/A"] if "Position" in filtered_roster.columns else []
                team_pos_f = st.selectbox("Filter by Position", ["All Positions"] + sorted(positions), key="team_cmj_pos_filter")

            team_cmj_rows = []
            for ath_name in sorted(cmj_data["Name"].unique()):
                ath_sub_cmj = cmj_data[cmj_data["Name"] == ath_name].sort_values("Date")
                if ath_sub_cmj.empty:
                    continue

                meta_row = filtered_roster[filtered_roster["Name"] == ath_name]
                pos_str = meta_row["Position"].iloc[0] if not meta_row.empty and "Position" in meta_row.columns else "N/A"
                photo_url = meta_row["Picture"].iloc[0] if not meta_row.empty and "Picture" in meta_row.columns else "https://www.w3schools.com/howto/img_avatar.png"
                
                if team_pos_f != "All Positions" and pos_str != team_pos_f:
                    continue

                ath_date_match = ath_sub_cmj[ath_sub_cmj["Date_Str"] == sel_team_cmj_date]
                if ath_date_match.empty:
                    continue

                readiness_pct = int(round(calc_wellness_for_date(ath_sub_cmj, sel_team_cmj_date)))
                z_color = get_readiness_color(readiness_pct)
                
                team_cmj_rows.append({
                    "Athlete": ath_name,
                    "Picture": photo_url,
                    "Position": pos_str,
                    "Readiness %": readiness_pct,
                    "Status_Color": z_color,
                })

            if team_cmj_rows:
                cmj_team_df = pd.DataFrame(team_cmj_rows).sort_values("Readiness %", ascending=False)
                c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                avg_team_readiness = cmj_team_df["Readiness %"].mean()
                peak_count = sum(1 for r in team_cmj_rows if r["Readiness %"] >= 90)
                fatigue_count = sum(1 for r in team_cmj_rows if r["Readiness %"] < 80)

                c_kpi1.metric("Athletes Evaluated", len(team_cmj_rows))
                c_kpi2.metric("Team Mean Wellness", f"{avg_team_readiness:.1f}%")
                c_kpi3.metric("Optimal (>=90%)", peak_count)
                c_kpi4.metric("Fatigued (<80%)", fatigue_count)

                team_tbl_html = """<table class="scout-table" style="width:100%; border:1px solid #E2E8F0; background:white; margin-top:15px;"><thead><tr style="background:#4895DB; color:white;"><th style="width:60px;">Athlete</th><th style="text-align:left !important; padding-left:15px;">Name</th><th>Position</th><th>Wellness Score</th></tr></thead><tbody>"""
                for _, row in cmj_team_df.iterrows():
                    team_tbl_html += f"""<tr>
                        <td style="padding:6px;"><img src="{row['Picture']}" style="width:38px; height:38px; border-radius:50%; object-fit:contain; border:2px solid #FF8200;"></td>
                        <td style="text-align:left !important; font-weight:800; padding-left:15px; font-size:13px;">{row['Athlete']}</td>
                        <td style="font-weight:600; color:#4B5563;">{row['Position']}</td>
                        <td style="font-weight:900; font-size:15px; color:{row['Status_Color']};">{row['Readiness %']}%</td>
                    </tr>"""
                team_tbl_html += "</tbody></table>"
                st.markdown(team_tbl_html, unsafe_allow_html=True)
            else:
                st.info(f"No Countermovement Jump testing records logged on {sel_team_cmj_date}.")


# ==========================================
# SECTION 5D: OVERALL PROFILE
# ==========================================
with testing_tab_overall:
    st.markdown(
        f'<div class="vball-section-title">Master Athletic Performance Summary ({season_label})</div>',
        unsafe_allow_html=True,
    )
    c_ov_ath, _ = st.columns([1, 2])
    with c_ov_ath:
        selected_ov_athlete = st.selectbox(
            "Select Athlete for Master Profile:",
            roster_players,
            key=f"overall_ath_select_{season_key}",
        )

    records = []

    def get_formatted_peak_overall(df_sub):
        if df_sub.empty:
            return None, None
        
        l_col = next((c for c in df_sub.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
        r_col = next((c for c in df_sub.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
        
        if l_col and r_col:
            df_sub["Peak_Val"] = df_sub[[l_col, r_col]].apply(pd.to_numeric, errors="coerce").max(axis=1)
            valid_rows = df_sub.dropna(subset=["Peak_Val"])
            if valid_rows.empty:
                return None, None
            
            best_row = valid_rows.sort_values("Peak_Val", ascending=False).iloc[0]
            l_val = pd.to_numeric(best_row[l_col], errors="coerce")
            r_val = pd.to_numeric(best_row[r_col], errors="coerce")
            
            l_str = f"{l_val:.1f} N" if pd.notna(l_val) else "N/A"
            r_str = f"{r_val:.1f} N" if pd.notna(r_val) else "N/A"
            
            return f"{l_str} / {r_str}", format_date_clean(best_row.get("Date"))
        else:
            return None, None

    p_cmj_ov = cmj_data[cmj_data["Name"] == selected_ov_athlete] if not cmj_data.empty and "Name" in cmj_data.columns else pd.DataFrame()
    if not p_cmj_ov.empty:
        jh_c = next((c for c in p_cmj_ov.columns if "jump" in c.lower() or "height" in c.lower()), None)
        if jh_c:
            p_cmj_ov["JH_Val"] = pd.to_numeric(p_cmj_ov[jh_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            valid_cmj = p_cmj_ov.dropna(subset=["JH_Val"])
            if not valid_cmj.empty:
                best_cmj = valid_cmj.sort_values("JH_Val", ascending=False).iloc[0]
                records.append({
                    "Category": "Countermovement Jump",
                    "Best Test Value": f"{best_cmj['JH_Val']:.2f} cm",
                    "Date Achieved": format_date_clean(best_cmj.get("Date"))
                })

    p_nord_ov = nordic_data[nordic_data["Name"] == selected_ov_athlete].copy() if not nordic_data.empty and "Name" in nordic_data.columns else pd.DataFrame()
    if not p_nord_ov.empty:
        t_c = next((c for c in p_nord_ov.columns if "test" in c.lower()), None)
        if t_c:
            for test_type_val in p_nord_ov[t_c].dropna().unique():
                sub_df = p_nord_ov[p_nord_ov[t_c] == test_type_val]
                val, dt = get_formatted_peak_overall(sub_df)
                if val:
                    records.append({
                        "Category": f"NordBord - {test_type_val} (L/R)",
                        "Best Test Value": val,
                        "Date Achieved": dt
                    })
        else:
            val, dt = get_formatted_peak_overall(p_nord_ov)
            if val:
                records.append({
                    "Category": "NordBord Hamstring (L/R)",
                    "Best Test Value": val,
                    "Date Achieved": dt
                })

    p_bs_ov = belt_squat_data[belt_squat_data["Name"] == selected_ov_athlete].copy() if not belt_squat_data.empty and "Name" in belt_squat_data.columns else pd.DataFrame()
    if not p_bs_ov.empty:
        f_c = next((c for c in p_bs_ov.columns if "peak vertical force" in c.lower() or "force" in c.lower()), None)
        if f_c:
            p_bs_ov["PVF"] = pd.to_numeric(p_bs_ov[f_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            valid_bs = p_bs_ov.dropna(subset=["PVF"])
            if not valid_bs.empty:
                best_bs = valid_bs.sort_values("PVF", ascending=False).iloc[0]
                records.append({
                    "Category": "Harness Belt Squat",
                    "Best Test Value": f"{best_bs['PVF']:.1f} N",
                    "Date Achieved": format_date_clean(best_bs.get("Date"))
                })

    p_knee_ov = knee_data[knee_data["Name"] == selected_ov_athlete].copy() if not knee_data.empty and "Name" in knee_data.columns else pd.DataFrame()
    if not p_knee_ov.empty:
        dir_col = next((c for c in p_knee_ov.columns if "direction" in c.lower() or "test" in c.lower()), None)
        ke_df = p_knee_ov[p_knee_ov[dir_col].astype(str).str.contains("Extension", case=False, na=False)] if dir_col else p_knee_ov
        kf_df = p_knee_ov[p_knee_ov[dir_col].astype(str).str.contains("Flexion", case=False, na=False)] if dir_col else pd.DataFrame()

        val, dt = get_formatted_peak_overall(ke_df)
        if val:
            records.append({"Category": "Knee Extension (L/R)", "Best Test Value": val, "Date Achieved": dt})

        val, dt = get_formatted_peak_overall(kf_df)
        if val:
            records.append({"Category": "Knee Flexion (L/R)", "Best Test Value": val, "Date Achieved": dt})

    p_hip_ov = hip_data[hip_data["Name"] == selected_ov_athlete].copy() if not hip_data.empty and "Name" in hip_data.columns else pd.DataFrame()
    if not p_hip_ov.empty:
        dir_col = next((c for c in p_hip_ov.columns if "direction" in c.lower() or "test" in c.lower()), None)
        ad_df = p_hip_ov[p_hip_ov[dir_col].astype(str).str.contains("AD|Adduction", case=False, na=False)] if dir_col else p_hip_ov
        ab_df = p_hip_ov[p_hip_ov[dir_col].astype(str).str.contains("AB|Abduction", case=False, na=False)] if dir_col else pd.DataFrame()

        val, dt = get_formatted_peak_overall(ad_df)
        if val:
            records.append({"Category": "Hip Adduction (L/R)", "Best Test Value": val, "Date Achieved": dt})

        val, dt = get_formatted_peak_overall(ab_df)
        if val:
            records.append({"Category": "Hip Abduction (L/R)", "Best Test Value": val, "Date Achieved": dt})

    p_ank_ov = ankle_data[ankle_data["Name"] == selected_ov_athlete].copy() if not ankle_data.empty and "Name" in ankle_data.columns else pd.DataFrame()
    if not p_ank_ov.empty:
        val, dt = get_formatted_peak_overall(p_ank_ov)
        if val:
            records.append({"Category": "Ankle Plantar Flexion (L/R)", "Best Test Value": val, "Date Achieved": dt})

    if records:
        ov_df = pd.DataFrame(records)
        st.markdown(f"### Peak Performance Snapshot for {selected_ov_athlete} ({season_label})")
        st.markdown(render_vball_table(ov_df), unsafe_allow_html=True)
    else:
        st.info(f"No testing records found across modules for {selected_ov_athlete} in {season_label}.")
