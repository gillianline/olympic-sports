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
    df_dj = pd.read_csv(st.secrets["sheet_drop_jump"]) 
    df_ash = pd.read_csv(st.secrets["sheet_ash"]) 
    
    # Clean up column names: remove hidden spaces and fix capitalization
    for df in [df_ff, df_roster, df_cmj, df_bs, df_nb, df_dj, df_ash]:
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
    df_dj = smart_merge(df_dj, df_roster)
    df_ash = smart_merge(df_ash, df_roster)
    
    return df_ff, df_cmj, df_bs, df_nb, df_dj, df_ash, df_roster

try:
    df_forceframe, df_cmj_full, df_bs_full, df_nb_full, df_dj_full, df_ash_full, df_roster = load_data()
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
for df in [df_roster, df_forceframe, df_cmj_full, df_bs_full, df_nb_full, df_dj_full, df_ash_full]:
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
filtered_dj = df_dj_full.copy()
filtered_ash = df_ash_full.copy()

# Apply Season Filter Downstream
if selected_season != "All Seasons":
    if 'Season' in filtered_ff.columns: filtered_ff = filtered_ff[filtered_ff['Season'].astype(str) == selected_season]
    if 'Season' in filtered_cmj.columns: filtered_cmj = filtered_cmj[filtered_cmj['Season'].astype(str) == selected_season]
    if 'Season' in filtered_bs.columns: filtered_bs = filtered_bs[filtered_bs['Season'].astype(str) == selected_season]
    if 'Season' in filtered_nb.columns: filtered_nb = filtered_nb[filtered_nb['Season'].astype(str) == selected_season]
    if 'Season' in filtered_dj.columns: filtered_dj = filtered_dj[filtered_dj['Season'].astype(str) == selected_season]
    if 'Season' in filtered_ash.columns: filtered_ash = filtered_ash[filtered_ash['Season'].astype(str) == selected_season]

# Apply Sport Filter Downstream
if selected_sport != "All Sports":
    if 'Sport' in filtered_ff.columns: filtered_ff = filtered_ff[filtered_ff['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_cmj.columns: filtered_cmj = filtered_cmj[filtered_cmj['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_bs.columns: filtered_bs = filtered_bs[filtered_bs['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_nb.columns: filtered_nb = filtered_nb[filtered_nb['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_dj.columns: filtered_dj = filtered_dj[filtered_dj['Sport'].astype(str) == selected_sport]
    if 'Sport' in filtered_ash.columns: filtered_ash = filtered_ash[filtered_ash['Sport'].astype(str) == selected_sport]

# Apply Player Filter Downstream
if selected_player != "All Players":
    filtered_ff = filtered_ff[filtered_ff['Name'].astype(str) == selected_player]
    filtered_cmj = filtered_cmj[filtered_cmj['Name'].astype(str) == selected_player]
    filtered_bs = filtered_bs[filtered_bs['Name'].astype(str) == selected_player]
    filtered_nb = filtered_nb[filtered_nb['Name'].astype(str) == selected_player]
    filtered_dj = filtered_dj[filtered_dj['Name'].astype(str) == selected_player]
    filtered_ash = filtered_ash[filtered_ash['Name'].astype(str) == selected_player]

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
    """Simple HTML table formatter to match CSS classes"""
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

# ---- BELT SQUAT DATA PREP ----
if not filtered_bs.empty and 'Date' in filtered_bs.columns:
    filtered_bs['Date'] = pd.to_datetime(filtered_bs['Date'], errors='coerce')
    filtered_bs['Date_Str'] = filtered_bs['Date'].dt.strftime("%m/%d/%y")
belt_squat_data = filtered_bs.copy()

# ---- CMJ DATA PREP ----
filtered_cmj['Date'] = pd.to_datetime(filtered_cmj['Date'], errors='coerce')
filtered_cmj['Date_Str'] = filtered_cmj['Date'].dt.strftime("%m/%d/%y")
cmj_data = filtered_cmj.copy()

# ---- DROP JUMP DATA PREP ----
if not filtered_dj.empty and 'Date' in filtered_dj.columns:
    filtered_dj['Date'] = pd.to_datetime(filtered_dj['Date'], errors='coerce')
    filtered_dj['Date_Str'] = filtered_dj['Date'].dt.strftime("%m/%d/%y")
dj_data = filtered_dj.copy()

# ---- ASH TEST DATA PREP ----
if not filtered_ash.empty and 'Date' in filtered_ash.columns:
    filtered_ash['Date'] = pd.to_datetime(filtered_ash['Date'], errors='coerce')
    filtered_ash['Date_Str'] = filtered_ash['Date'].dt.strftime("%m/%d/%y")
ash_data = filtered_ash.copy()

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
    ["Intake Assessment", "Jump Testing", "Wellness Score", "Overall Profile"]
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
    dj_ath_intake = dj_data[dj_data["Name"] == selected_intake_athlete].sort_values("Date") if not dj_data.empty and "Name" in dj_data.columns else pd.DataFrame()
    ash_ath_intake = ash_data[ash_data["Name"] == selected_intake_athlete].sort_values("Date") if not ash_data.empty and "Name" in ash_data.columns else pd.DataFrame()

    has_data = not (calf_ath.empty and hip_ath.empty and sh_ath.empty and nord_ath.empty and bs_ath.empty and dj_ath_intake.empty and ash_ath_intake.empty)

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
        # Dynamic Anatomical SVG Pointers Based on Data Presence
        node_6_svg = """
        <!-- 6. Shoulder (ASH Test) - Right Side -->
        <line x1="84" y1="44" x2="112" y2="44" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="84" cy="44" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="36" width="16" height="16" rx="4" fill="#4895DB" />
        <text x="120" y="48" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">6</text>
        """ if not ash_ath_intake.empty else ""

        node_1_svg = """
        <!-- 1. Belt Squat (Core / Waist) - Right Side -->
        <line x1="68" y1="84" x2="112" y2="84" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="68" cy="84" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="76" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="88" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
        """ if not bs_ath.empty else ""
        
        node_2_svg = """
        <!-- 2. Hip (AD/AB) - Left Side -->
        <line x1="50" y1="106" x2="24" y2="106" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="50" cy="106" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="8" y="98" width="16" height="16" rx="4" fill="#4895DB" />
        <text x="16" y="110" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>
        """ if not hip_ath.empty else ""
        
        node_4_svg = """
        <!-- 4. Hamstring (NordBord) - Left Side -->
        <line x1="52" y1="135" x2="24" y2="135" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="52" cy="135" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="8" y="127" width="16" height="16" rx="4" fill="#4895DB" />
        <text x="16" y="139" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>
        """ if not nord_ath.empty else ""

        node_3_svg = """
        <!-- 3. Knee (Ext/Flex) - Right Side -->
        <line x1="82" y1="148" x2="112" y2="148" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="82" cy="148" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="140" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="152" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>
        """ if not sh_ath.empty else ""
        
        node_5_svg = """
        <!-- 5. Ankle - Right Side -->
        <line x1="80" y1="185" x2="112" y2="185" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="80" cy="185" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="112" y="177" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="120" y="189" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
        """ if not calf_ath.empty else ""

        node_7_svg = """
        <!-- 7. Drop Jump (Feet) - Left Side -->
        <line x1="68" y1="208" x2="24" y2="208" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
        <circle cx="68" cy="208" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
        <rect x="8" y="200" width="16" height="16" rx="4" fill="#FF8200" />
        <text x="16" y="212" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">7</text>
        """ if not dj_ath_intake.empty else ""

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
                    {node_6_svg}
                    {node_1_svg}
                    {node_2_svg}
                    {node_4_svg}
                    {node_3_svg}
                    {node_5_svg}
                    {node_7_svg}
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
            # 6. ASH TEST (Matches Node 6 - Shoulders)
            if not ash_ath_intake.empty:
                iso_col = next((c for c in ash_ath_intake.columns if "isometric type" in c.lower()), None)
                pos_col = next((c for c in ash_ath_intake.columns if "position" in c.lower()), None)
                l_col = next((c for c in ash_ath_intake.columns if "force" in c.lower() and "(l)" in c.lower()), None)
                r_col = next((c for c in ash_ath_intake.columns if "force" in c.lower() and "(r)" in c.lower()), None)

                if iso_col and pos_col and l_col and r_col:
                    ash_ath_intake_clean = ash_ath_intake.copy()
                    ash_ath_intake_clean[pos_col] = ash_ath_intake_clean[pos_col].fillna("None").replace("", "None")
                    
                    combos = ash_ath_intake_clean[[iso_col, pos_col]].drop_duplicates().sort_values(by=[iso_col, pos_col])
                    
                    ash_html = ""
                    date_str = format_date_clean(ash_ath_intake.sort_values("Date").iloc[-1].get("Date"))

                    for _, row in combos.iterrows():
                        itype = row[iso_col]
                        ipos = row[pos_col]
                        sub_df = ash_ath_intake_clean[(ash_ath_intake_clean[iso_col] == itype) & (ash_ath_intake_clean[pos_col] == ipos)]
                        
                        (maxL, maxR), (recL, recR), _ = get_peak_and_recent_row(sub_df, l_col, r_col)
                        
                        divider = '<div style="margin-top:6px; margin-bottom:6px; border-bottom:1px solid #D5E5E8;"></div>' if ash_html != "" else ""
                        ash_html += f"{divider}<b>{itype} ({ipos}):</b> Max L {maxL:.1f}N | R {maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(recL, maxL, '{:.1f}', 'N')} | R {render_val_with_arrow(recR, maxR, '{:.1f}', 'N')}<br>"
                
                    if ash_html != "":
                        st.markdown(
                            f"""
                            <div class="hud-metric-row-light-blue">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">6</span>ASH</span>
                                    <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                </div>
                                <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                    {ash_html}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

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

            # 7. DROP JUMP (Matches Node 7 - Feet/Ground)
            if not dj_ath_intake.empty:
                dj_jh_col = next((c for c in dj_ath_intake.columns if "jump height" in c.lower()), None)
                dj_rsi_col = next((c for c in dj_ath_intake.columns if "rsi" in c.lower()), None)
                
                dj_jh_max = pd.to_numeric(dj_ath_intake[dj_jh_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce").max() if dj_jh_col else 0
                dj_jh_rec = pd.to_numeric(dj_ath_intake.sort_values("Date").iloc[-1].get(dj_jh_col, 0), errors="coerce") if dj_jh_col else 0
                
                dj_rsi_max = pd.to_numeric(dj_ath_intake[dj_rsi_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce").max() if dj_rsi_col else 0
                dj_rsi_rec = pd.to_numeric(dj_ath_intake.sort_values("Date").iloc[-1].get(dj_rsi_col, 0), errors="coerce") if dj_rsi_col else 0

                date_str = format_date_clean(dj_ath_intake.sort_values("Date").iloc[-1].get("Date"))

                st.markdown(
                    f"""
                    <div class="hud-metric-row-light">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">7</span>DROP JUMP</span>
                            <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                        </div>
                        <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                            <b>Jump Height:</b> Max {dj_jh_max:.1f}cm &nbsp;→&nbsp; <b>Recent:</b> {render_val_with_arrow(dj_jh_rec, dj_jh_max, '{:.1f}', 'cm')}<br>
                            <b>RSI:</b> Max {dj_rsi_max:.2f} &nbsp;→&nbsp; <b>Recent:</b> {render_val_with_arrow(dj_rsi_rec, dj_rsi_max, '{:.2f}', '')}
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

        if not ash_ath_intake.empty:
            with st.expander("ASH Log", expanded=False):
                target_cols_ash = [
                    "Date", "Test Type", "Isometric Type", "Position", 
                    "Peak Vertical Force [N] (L)", "Peak Vertical Force [N] (R)", 
                    "Peak Vertical Force [N] (Asym)(%)"
                ]
                final_cols_ash = [c for c in target_cols_ash if c in ash_ath_intake.columns]
                df_ash_display = ash_ath_intake[final_cols_ash].copy()
                if "Date" in df_ash_display.columns:
                    df_ash_display["Date"] = pd.to_datetime(df_ash_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")
                for col in df_ash_display.columns:
                    if "Force" in col or "Asym" in col:
                        df_ash_display[col] = pd.to_numeric(df_ash_display[col], errors="coerce").apply(lambda x: f"{x:.1f}" if pd.notna(x) else pd.NA)
                df_ash_display = df_ash_display.dropna(axis=1, how='all').fillna("-")
                st.dataframe(df_ash_display, use_container_width=True, hide_index=True)

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
                
        if not dj_ath_intake.empty:
            with st.expander("Drop Jump Log", expanded=False):
                target_cols_dj = ["Test Type", "Date", "BW [KG]", "Drop Height [cm]"]
                dj_rsi_col = next((c for c in dj_ath_intake.columns if "rsi" in c.lower()), None)
                dj_jh_col = next((c for c in dj_ath_intake.columns if "jump height" in c.lower()), None)
                if dj_rsi_col: target_cols_dj.append(dj_rsi_col)
                if dj_jh_col: target_cols_dj.append(dj_jh_col)
                target_cols_dj.extend(["Contact Time [s]", "Effective Drop [cm]"])
                
                final_cols_dj = [c for c in target_cols_dj if c in dj_ath_intake.columns]
                df_dj_display = dj_ath_intake[final_cols_dj].copy()
                
                rename_map_dj = {}
                if dj_jh_col: rename_map_dj[dj_jh_col] = "Jump Height (cm)"
                if dj_rsi_col: rename_map_dj[dj_rsi_col] = "RSI [m/s]"
                df_dj_display = df_dj_display.rename(columns=rename_map_dj)
                
                if "Date" in df_dj_display.columns:
                    df_dj_display["Date"] = pd.to_datetime(df_dj_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")

                for col in df_dj_display.columns:
                    if col not in ["Test Type", "Date"]:
                        df_dj_display[col] = pd.to_numeric(df_dj_display[col], errors="coerce").apply(lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA)
                
                df_dj_display = df_dj_display.dropna(axis=1, how='all').fillna("-")
                st.dataframe(df_dj_display, use_container_width=True, hide_index=True)


# ==========================================
# SECTION 5B: JUMPS TAB (CMJ & DROP JUMP)
# ==========================================
with testing_tab_cmj:
    st.markdown(
        f'<div class="vball-section-title">Jump Testing Performance — {season_label}</div>',
        unsafe_allow_html=True,
    )

    c_filter, _ = st.columns([1, 2])
    with c_filter:
        selected_player_t = st.selectbox(
            "Select Athlete:", roster_players, key=f"jump_player_select_{season_key}"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- CMJ SECTION ---
    p_cmj = (
        cmj_data[cmj_data["Name"] == selected_player_t]
        .sort_values("Date")
        .copy()
        if not cmj_data.empty
        else pd.DataFrame()
    )

    if not p_cmj.empty:
        st.markdown(f"#### Countermovement Jump (CMJ) History")
        jump_cols = [c for c in p_cmj.columns if "jump" in c.lower() or "height" in c.lower()]
        j_col = jump_cols[0] if jump_cols else None
        rsi_cols = [c for c in p_cmj.columns if "rsi" in c.lower()]
        rsi_col = rsi_cols[0] if rsi_cols else None

        if j_col:
            p_cmj["Jump_Height_Clean"] = pd.to_numeric(p_cmj[j_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            
            fig_jump_trend = go.Figure()
            fig_jump_trend.add_trace(go.Scatter(
                x=p_cmj["Date"], y=p_cmj["Jump_Height_Clean"],
                name="Jump Height", mode="lines+markers", connectgaps=True,
                yaxis="y", line=dict(color="#FF8200", width=4), marker=dict(size=8, color="#FF8200"),
            ))

            if rsi_col:
                p_cmj["RSI_Clean"] = pd.to_numeric(p_cmj[rsi_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
                fig_jump_trend.add_trace(go.Scatter(
                    x=p_cmj["Date"], y=p_cmj["RSI_Clean"],
                    name="RSI Modified", mode="lines+markers", connectgaps=True,
                    yaxis="y2", line=dict(color="#38BDF8", width=3, dash="dot"), marker=dict(size=8, color="#38BDF8"),
                ))

            fig_jump_trend.update_layout(
                height=320, margin=dict(l=40, r=40, t=50, b=40),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0.01, font=dict(size=13, color="#0F172A")),
                xaxis=dict(title=None, type="date", tickformat="%b %d\n%Y", showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12)),
                yaxis=dict(showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12), side="left"),
                yaxis2=dict(showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12), overlaying="y", side="right", anchor="x"),
            )
            st.plotly_chart(fig_jump_trend, use_container_width=True, key=f"cmj_trend_{season_key}")

            target_cols = ["Test Type", "Date", "BW [KG]"]
            if j_col: target_cols.append(j_col)
            target_cols.extend(["Peak Power [W]", "Eccentric Braking RFD [N/s]"])
            if rsi_col: target_cols.append(rsi_col)
            target_cols.extend(["Concentric Peak Velocity [m/s]", "CMJ Stiffness [N/m]"])
            
            final_cols = [c for c in target_cols if c in p_cmj.columns]
            df_cmj_display = p_cmj[final_cols].copy()
            
            rename_map = {}
            if j_col: rename_map[j_col] = "Jump Height (cm)"
            if rsi_col: rename_map[rsi_col] = "RSI [m/s]"
            df_cmj_display = df_cmj_display.rename(columns=rename_map)
            
            if "Date" in df_cmj_display.columns:
                df_cmj_display["Date"] = pd.to_datetime(df_cmj_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")

            for col in df_cmj_display.columns:
                if col not in ["Test Type", "Date"]:
                    df_cmj_display[col] = pd.to_numeric(df_cmj_display[col], errors="coerce").apply(lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA)
            
            df_cmj_display = df_cmj_display.dropna(axis=1, how='all').fillna("-")
            st.dataframe(df_cmj_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"No Countermovement Jump (CMJ) logs found for {selected_player_t} in {season_label}.")       

    # --- DROP JUMP SECTION ---
    p_dj = (
        dj_data[dj_data["Name"] == selected_player_t]
        .sort_values("Date")
        .copy()
        if not dj_data.empty
        else pd.DataFrame()
    )
    
    if not p_dj.empty:
        st.divider()
        st.markdown(f"#### Drop Jump Performance History")
        
        dj_jh_col = next((c for c in p_dj.columns if "jump height" in c.lower()), None)
        dj_rsi_col = next((c for c in p_dj.columns if "rsi" in c.lower()), None)

        if dj_jh_col or dj_rsi_col:
            fig_dj_trend = go.Figure()
            
            if dj_jh_col:
                p_dj["DJ_JH_Clean"] = pd.to_numeric(p_dj[dj_jh_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
                fig_dj_trend.add_trace(go.Scatter(
                    x=p_dj["Date"], y=p_dj["DJ_JH_Clean"],
                    name="Jump Height", mode="lines+markers", connectgaps=True,
                    yaxis="y", line=dict(color="#FF8200", width=4), marker=dict(size=8, color="#FF8200"),
                ))

            if dj_rsi_col:
                p_dj["DJ_RSI_Clean"] = pd.to_numeric(p_dj[dj_rsi_col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
                fig_dj_trend.add_trace(go.Scatter(
                    x=p_dj["Date"], y=p_dj["DJ_RSI_Clean"],
                    name="RSI", mode="lines+markers", connectgaps=True,
                    yaxis="y2", line=dict(color="#38BDF8", width=3, dash="dot"), marker=dict(size=8, color="#38BDF8"),
                ))

            fig_dj_trend.update_layout(
                height=320, margin=dict(l=40, r=40, t=50, b=40),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0.01, font=dict(size=13, color="#0F172A")),
                xaxis=dict(title=None, type="date", tickformat="%b %d\n%Y", showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12)),
                yaxis=dict(showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12), side="left"),
                yaxis2=dict(showgrid=False, showline=True, linewidth=1.5, linecolor="#0F172A", tickfont=dict(color="#64748B", size=12), overlaying="y", side="right", anchor="x"),
            )
            st.plotly_chart(fig_dj_trend, use_container_width=True, key=f"dj_trend_{season_key}")

        target_cols_dj = ["Test Type", "Date", "BW [KG]", "Drop Height [cm]"]
        if dj_rsi_col: target_cols_dj.append(dj_rsi_col)
        if dj_jh_col: target_cols_dj.append(dj_jh_col)
        target_cols_dj.extend(["Contact Time [s]", "Effective Drop [cm]"])
        
        final_cols_dj = [c for c in target_cols_dj if c in p_dj.columns]
        df_dj_display = p_dj[final_cols_dj].copy()
        
        rename_map_dj = {}
        if dj_jh_col: rename_map_dj[dj_jh_col] = "Jump Height (cm)"
        if dj_rsi_col: rename_map_dj[dj_rsi_col] = "RSI [m/s]"
        df_dj_display = df_dj_display.rename(columns=rename_map_dj)
        
        if "Date" in df_dj_display.columns:
            df_dj_display["Date"] = pd.to_datetime(df_dj_display["Date"], errors='coerce').dt.strftime("%b %d, %Y")

        for col in df_dj_display.columns:
            if col not in ["Test Type", "Date"]:
                df_dj_display[col] = pd.to_numeric(df_dj_display[col], errors="coerce").apply(lambda x: f"{x:.2f}" if pd.notna(x) else pd.NA)
        
        df_dj_display = df_dj_display.dropna(axis=1, how='all').fillna("-")
        st.dataframe(df_dj_display, use_container_width=True, hide_index=True)


# ==========================================
# SECTION 5C: WELLNESS JUMP TAB
# ==========================================
with testing_tab_wellness:
    st.markdown(
        f'<div class="vball-section-title">Readiness & Wellness ({season_label})</div>',
        unsafe_allow_html=True,
    )
    
    # Helpers for the Wellness Score
    def calc_wellness_for_date(ath_cmj_df, target_date_str):
        df_s = ath_cmj_df.sort_values("Date").copy()
        
        target_df = df_s[df_s["Date_Str"] == target_date_str]
        if target_df.empty: return 0
        
        # Define the target metrics and their optimization direction (higher_better = True means a higher value is better)
        wellness_metrics = [
            {"keys": ["rsi-modified", "rsi"], "higher_better": True},
            {"keys": ["eccentric braking rfd"], "higher_better": True},
            {"keys": ["force at zero velocity", "force @ 0 velo"], "higher_better": True},
            {"keys": ["time to takeoff", "contraction time"], "higher_better": False},
            {"keys": ["p2 concentric impulse:p1 concentric", "p2:p1"], "higher_better": True}
        ]
        
        scores = []
        
        for m in wellness_metrics:
            # Find the matching column dynamically
            col = next((c for c in df_s.columns if any(k in c.lower() for k in m["keys"])), None)
            if not col: continue
            
            # Clean and format the column
            df_s[f"{col}_Clean"] = pd.to_numeric(df_s[col].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            valid_data = df_s.dropna(subset=[f"{col}_Clean"])
            
            if valid_data.empty: continue
            
            # Fetch latest value for this athlete specifically on the target date
            latest_row = valid_data[valid_data["Date_Str"] == target_date_str]
            if latest_row.empty: continue
            
            latest_val = latest_row.iloc[-1][f"{col}_Clean"]
            if pd.isna(latest_val) or latest_val <= 0: continue
            
            # Calculate % score based on direction 
            if m["higher_better"]:
                max_val = valid_data[f"{col}_Clean"].max()
                if max_val > 0:
                    scores.append((latest_val / max_val) * 100)
            else:
                min_val = valid_data[f"{col}_Clean"].min()
                if min_val > 0:
                    scores.append((min_val / latest_val) * 100)
                    
        if scores:
            return sum(scores) / len(scores)
        return 0

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
            
            # Map metrics with fuzzy keys and define inversion rule (lower is better = True)
            wellness_metrics_ref = [
                {"label": "mRSI", "keys": ["rsi-modified", "rsi"], "invert": False},
                {"label": "ECC_RFD", "keys": ["eccentric braking rfd"], "invert": False},
                {"label": "F0V", "keys": ["force at zero velocity", "force @ 0 velo"], "invert": False},
                {"label": "TTO", "keys": ["time to takeoff", "contraction time"], "invert": True},
                {"label": "P2P1", "keys": ["p2 concentric impulse:p1", "p2:p1"], "invert": True}
            ]

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

                target_row = ath_date_match.iloc[-1]
                cols = ath_sub_cmj.columns

                # Find the previous row for percentage comparison
                all_indices = list(ath_sub_cmj.index)
                if target_row.name in all_indices:
                    cur_pos = all_indices.index(target_row.name)
                    prev_row = ath_sub_cmj.iloc[max(0, cur_pos - 1)]
                else:
                    prev_row = target_row
                
                indiv_scores = {}
                sub_scores = []

                for rm in wellness_metrics_ref:
                    # Fuzzy match the column name
                    c_name = next((c for c in cols if any(k in c.lower() for k in rm["keys"])), None)
                    lbl = rm["label"]
                    
                    if c_name and c_name in target_row and c_name in prev_row:
                        try:
                            # Strip any text strings (like [m/s]) and convert to float
                            t_val = abs(float(pd.to_numeric(str(target_row.get(c_name, 0.0)).replace(r"[^0-9.-]", ""), errors="coerce")))
                            s_val = abs(float(pd.to_numeric(str(prev_row.get(c_name, 0.0)).replace(r"[^0-9.-]", ""), errors="coerce")))
                            
                            if s_val > 0 and t_val > 0:
                                pct_diff = ((t_val - s_val) / s_val) * 100.0
                                score = (100.0 - pct_diff) if rm["invert"] else (100.0 + pct_diff)
                                score = max(0.0, min(100.0, score))
                                indiv_scores[lbl] = score
                                sub_scores.append(score)
                            else:
                                indiv_scores[lbl] = None
                        except Exception:
                            indiv_scores[lbl] = None
                    else:
                        indiv_scores[lbl] = None

                readiness_pct = int(round(sum(sub_scores) / len(sub_scores))) if sub_scores else 100
                z_color = get_readiness_color(readiness_pct)
                
                def format_pct(val):
                    return f"{int(round(val))}%" if val is not None else "-"
                    
                def get_pct_color(val):
                    if val is None: return "#1D1D1F"
                    if val >= 90: return "#15803D"
                    if val >= 80: return "#D97706"
                    return "#B91C1C"

                team_cmj_rows.append({
                    "Athlete": ath_name,
                    "Picture": photo_url,
                    "Position": pos_str,
                    "Readiness %": readiness_pct,
                    "Status_Color": z_color,
                    "mRSI": format_pct(indiv_scores.get("mRSI")),
                    "mRSI_c": get_pct_color(indiv_scores.get("mRSI")),
                    "Ecc_RFD": format_pct(indiv_scores.get("ECC_RFD")),
                    "Ecc_RFD_c": get_pct_color(indiv_scores.get("ECC_RFD")),
                    "F0V": format_pct(indiv_scores.get("F0V")),
                    "F0V_c": get_pct_color(indiv_scores.get("F0V")),
                    "Time_Takeoff": format_pct(indiv_scores.get("TTO")),
                    "TTO_c": get_pct_color(indiv_scores.get("TTO")),
                    "P2P1": format_pct(indiv_scores.get("P2P1")),
                    "P2P1_c": get_pct_color(indiv_scores.get("P2P1"))
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

                # Upgraded table with the 5 appended metrics and updated coloring
                team_tbl_html = """<table class="scout-table" style="width:100%; border:1px solid #E2E8F0; background:white; margin-top:15px; text-align:center; font-size:12px;">
                <thead>
                    <tr style="background:#FF8200; color:white;">
                        <th style="width:50px; padding:8px;">Photo</th>
                        <th style="text-align:left !important; padding-left:15px;">Name</th>
                        <th>Position</th>
                        <th style="background:#82C6E2; color:#0F172A;">Wellness Score</th>
                        <th>Readiness Status</th>
                        <th>RSI-Mod</th>
                        <th>Ecc Braking RFD</th>
                        <th>Force @ 0 Velo</th>
                        <th>Time to Takeoff</th>
                        <th>P2:P1 Ratio</th>
                    </tr>
                </thead><tbody>"""
                
                for _, row in cmj_team_df.iterrows():
                    r_val = row["Readiness %"]
                    status_text = "Optimal Readiness" if r_val >= 90 else ("Moderate Fatigue" if r_val >= 80 else "High Fatigue Risk")
                    badge_bg = "#DCFCE7" if r_val >= 90 else ("#FEF3C7" if r_val >= 80 else "#FEE2E2")
                    badge_fg = "#15803D" if r_val >= 90 else ("#B45309" if r_val >= 80 else "#B91C1C")

                    team_tbl_html += f"""<tr style="border-bottom: 1px solid #E2E8F0;">
                        <td style="padding:6px;"><img src="{row['Picture']}" style="width:38px; height:38px; border-radius:50%; object-fit:contain; border:2px solid #FF8200;"></td>
                        <td style="text-align:left !important; font-weight:800; padding-left:15px; font-size:13px; color:#1D1D1F;">{row['Athlete']}</td>
                        <td style="font-weight:600; color:#64748B;">{row['Position']}</td>
                        <td style="font-weight:900; font-size:15px; color:{row['Status_Color']}; background:#F8FAFC;">{row['Readiness %']}%</td>
                        <td><span style="background-color:{badge_bg}; color:{badge_fg}; padding:4px 10px; border-radius:12px; font-weight:700; font-size:0.75rem; white-space:nowrap;">{status_text}</span></td>
                        <td style="font-weight:800; color:{row['mRSI_c']};">{row['mRSI']}</td>
                        <td style="font-weight:800; color:{row['Ecc_RFD_c']};">{row['Ecc_RFD']}</td>
                        <td style="font-weight:800; color:{row['F0V_c']};">{row['F0V']}</td>
                        <td style="font-weight:800; color:{row['TTO_c']};">{row['Time_Takeoff']}</td>
                        <td style="font-weight:800; color:{row['P2P1_c']};">{row['P2P1']}</td>
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

    p_ash_ov = ash_data[ash_data["Name"] == selected_ov_athlete] if not ash_data.empty and "Name" in ash_data.columns else pd.DataFrame()
    if not p_ash_ov.empty:
        iso_c = next((c for c in p_ash_ov.columns if "isometric type" in c.lower()), None)
        pos_c = next((c for c in p_ash_ov.columns if "position" in c.lower()), None)
        l_col = next((c for c in p_ash_ov.columns if "force" in c.lower() and "(l)" in c.lower()), None)
        r_col = next((c for c in p_ash_ov.columns if "force" in c.lower() and "(r)" in c.lower()), None)
        if iso_c and pos_c and l_col and r_col:
            p_ash_ov_clean = p_ash_ov.copy()
            p_ash_ov_clean[pos_c] = p_ash_ov_clean[pos_c].fillna("None").replace("", "None")
            p_ash_ov_clean["Peak_Val"] = p_ash_ov_clean[[l_col, r_col]].apply(pd.to_numeric, errors="coerce").max(axis=1)
            combos = p_ash_ov_clean[[iso_c, pos_c]].drop_duplicates()
            for _, row in combos.iterrows():
                itype = row[iso_c]
                ipos = row[pos_c]
                sub_df = p_ash_ov_clean[(p_ash_ov_clean[iso_c] == itype) & (p_ash_ov_clean[pos_c] == ipos)]
                valid_ash = sub_df.dropna(subset=["Peak_Val"])
                if not valid_ash.empty:
                    best_ash = valid_ash.sort_values("Peak_Val", ascending=False).iloc[0]
                    l_val = pd.to_numeric(best_ash[l_col], errors="coerce")
                    r_val = pd.to_numeric(best_ash[r_col], errors="coerce")
                    records.append({
                        "Category": f"ASH Test - {itype} ({ipos})",
                        "Best Test Value": f"{l_val:.1f} N / {r_val:.1f} N",
                        "Date Achieved": format_date_clean(best_ash.get("Date"))
                    })

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

    p_dj_ov = dj_data[dj_data["Name"] == selected_ov_athlete] if not dj_data.empty and "Name" in dj_data.columns else pd.DataFrame()
    if not p_dj_ov.empty:
        dj_jh_c = next((c for c in p_dj_ov.columns if "jump height" in c.lower()), None)
        if dj_jh_c:
            p_dj_ov["DJ_JH_Val"] = pd.to_numeric(p_dj_ov[dj_jh_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            valid_dj_jh = p_dj_ov.dropna(subset=["DJ_JH_Val"])
            if not valid_dj_jh.empty:
                best_dj = valid_dj_jh.sort_values("DJ_JH_Val", ascending=False).iloc[0]
                records.append({
                    "Category": "Drop Jump - Max Height",
                    "Best Test Value": f"{best_dj['DJ_JH_Val']:.2f} cm",
                    "Date Achieved": format_date_clean(best_dj.get("Date"))
                })
        dj_rsi_c = next((c for c in p_dj_ov.columns if "rsi" in c.lower()), None)
        if dj_rsi_c:
            p_dj_ov["DJ_RSI_Val"] = pd.to_numeric(p_dj_ov[dj_rsi_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce")
            valid_dj_rsi = p_dj_ov.dropna(subset=["DJ_RSI_Val"])
            if not valid_dj_rsi.empty:
                best_rsi = valid_dj_rsi.sort_values("DJ_RSI_Val", ascending=False).iloc[0]
                records.append({
                    "Category": "Drop Jump - Max RSI",
                    "Best Test Value": f"{best_rsi['DJ_RSI_Val']:.2f} m/s",
                    "Date Achieved": format_date_clean(best_rsi.get("Date"))
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
