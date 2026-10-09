import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime

# Set page layout to wide to match typical testing dashboards
st.set_page_config(page_title="Soccer Testing Dashboard", layout="wide", page_icon="⚽")

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
        st.title("🔒 Dashboard Login")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.title("🔒 Dashboard Login")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    
    return True # Password correct!

# Stop execution if password fails
if not check_password():
    st.stop()

# ==========================================
# 2. LOAD SECRET DATA
# ==========================================
@st.cache_data(ttl=600) # Caches data for 10 minutes so it doesn't reload every click
def load_data():
    # Load from the secret URLs in your secrets.toml
    # (Using pandas to read the CSV export of a Google Sheet or private server)
    df_ff = pd.read_csv(st.secrets["sheet_forceframe"])
    df_roster = pd.read_csv(st.secrets["sheet_roster"])
    
    # Ensure Name column is treated as strings for matching
    df_ff['Name'] = df_ff['Name'].astype(str)
    df_roster['Name'] = df_roster['Name'].astype(str)
    
    # Merge Roster info (Team, Position) into ForceFrame data based on Name
    df_ff = pd.merge(df_ff, df_roster, on="Name", how="left")
    
    return df_ff, df_roster

try:
    df_forceframe, df_roster = load_data()
except Exception as e:
    st.error("Error loading secure data. Please check your sheet links in secrets.toml.")
    st.stop()


# ==========================================
# 3. DASHBOARD UI & SIDEBAR
# ==========================================
st.title("⚽ Soccer Testing Dashboard")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("Filter Options")

# Sport Filter (Replaces Team)
if 'Sport' in df_roster.columns:
    sports = df_roster['Sport'].dropna().unique().tolist()
    selected_sport = st.sidebar.selectbox("Select Sport", ["All Sports"] + sports)
else:
    selected_sport = "All Sports"

# Player Filter (dependent on Sport)
if selected_sport != "All Sports":
    filtered_roster = df_roster[df_roster['Sport'] == selected_sport]
else:
    filtered_roster = df_roster

players = filtered_roster['Name'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select Player", ["All Players"] + players)

# Filter the ForceFrame Data based on selections
filtered_ff = df_forceframe.copy()
if selected_sport != "All Sports" and 'Sport' in filtered_ff.columns:
    filtered_ff = filtered_ff[filtered_ff['Sport'] == selected_sport]
if selected_player != "All Players":
    filtered_ff = filtered_ff[filtered_ff['Name'] == selected_player]
    
# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def format_date_clean(date_val):
    if pd.isna(date_val): return "N/A"
    try:
        # Assumes date is something like '9/11/26'
        dt = pd.to_datetime(date_val)
        return dt.strftime("%b %d, %Y")
    except:
        return str(date_val)

def render_vball_table(df):
    """Simple HTML table formatter to match your CSS classes"""
    return df.to_html(classes="table table-striped", index=False, escape=False)

def render_cmj_tscore_standards(player, raw_df, target_date_str, widget_key_suffix):
    """Placeholder for your CMJ T-Score standard renderer"""
    st.info("CMJ Standards Module goes here (Requires CMJ Data Sheet)")

# ==========================================
# 5. DATA PREPARATION FOR HUD
# ==========================================
df_forceframe['Date'] = pd.to_datetime(df_forceframe['Date'], errors='coerce')
df_forceframe['Date_Str'] = df_forceframe['Date'].dt.strftime("%m/%d/%y")

# Split by the specific tests in your soccer sheet
ankle_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Ankle', na=False, case=False)]
knee_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Knee', na=False, case=False)]
hip_ad_ab_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Hip AD/AB', na=False, case=False)]
hip_ir_er_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Hip IR/ER', na=False, case=False)]
shoulder_data = df_forceframe[df_forceframe['Test'].astype(str).str.contains('Shoulder', na=False, case=False)]

# Variables expected by your snippet
season_label = "2026 Season"
season_key = "soc26"
roster_players = df_roster['Name'].dropna().unique().tolist()

# ==========================================
# 6. DASHBOARD UI (THE TESTING TAB)
# ==========================================

# We will put your code inside the first tab to keep the structure clean
testing_tab, roster_tab, empty_tab1, empty_tab2 = st.tabs([
    "Testing HUD", "Roster", "Sheet 3", "Sheet 4"
])

with testing_tab:
    # --- START OF YOUR EXACT SNIPPET ---
    testing_tab_intake, testing_tab_cmj, testing_tab_overall = st.tabs(
        ["Intake Assessment", "CMJ", "Overall Profile"]
    )

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
            hud_svg_html = """
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
                        <line x1="82" y1="58" x2="112" y2="58" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                        <circle cx="82" cy="58" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                        <rect x="112" y="50" width="16" height="16" rx="4" fill="#FF8200" />
                        <text x="120" y="62" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
                        <line x1="58" y1="116" x2="24" y2="116" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
                        <circle cx="58" cy="116" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
                        <rect x="8" y="108" width="16" height="16" rx="4" fill="#4895DB" />
                        <text x="16" y="120" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>
                        <line x1="74" y1="172" x2="112" y2="172" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
                        <circle cx="74" cy="172" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
                        <rect x="112" y="164" width="16" height="16" rx="4" fill="#4895DB" />
                        <text x="120" y="176" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>
                        <line x1="60" y1="140" x2="24" y2="140" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                        <circle cx="60" cy="140" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                        <rect x="8" y="132" width="16" height="16" rx="4" fill="#FF8200" />
                        <text x="16" y="144" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>
                        <line x1="68" y1="84" x2="112" y2="84" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
                        <circle cx="68" cy="84" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
                        <rect x="112" y="76" width="16" height="16" rx="4" fill="#4895DB" />
                        <text x="120" y="88" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
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
                if not sh_ath.empty:
                    l_col = next((c for c in sh_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                    r_col = next((c for c in sh_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                    dir_c = next((c for c in sh_ath.columns if "direction" in c.lower() or "test" in c.lower()), None)
                    knee_ext = sh_ath[sh_ath[dir_c].astype(str).str.contains("Extension", case=False, na=False)] if dir_c else sh_ath
                    knee_flx = sh_ath[sh_ath[dir_c].astype(str).str.contains("Flexion", case=False, na=False)] if dir_c else sh_ath

                    (ke_maxL, ke_maxR), (ke_recL, ke_recR), (ke_initL, ke_initR) = get_peak_and_recent_row(knee_ext, l_col, r_col)
                    (kf_maxL, kf_maxR), (kf_recL, kf_recR), (kf_initL, kf_initR) = get_peak_and_recent_row(knee_flx, l_col, r_col)
                    latest_date_str = format_date_clean(knee_ext.sort_values("Date").iloc[-1].get("Date")) if not knee_ext.empty else "N/A"

                    st.markdown(
                        f"""
                        <div class="hud-metric-row-light">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">1</span>KNEE EXTENSION & FLEXION</span>
                                <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {latest_date_str}</span>
                            </div>
                            <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                <b>Extension:</b> Max L {ke_maxL:.1f}N | R {ke_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ke_recL, ke_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(ke_recR, ke_initR, '{:.1f}', 'N')}<br>
                                <b>Flexion:</b> Max L {kf_maxL:.1f}N | R {kf_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(kf_recL, kf_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(kf_recR, kf_initR, '{:.1f}', 'N')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if not hip_ath.empty:
                    l_col = next((c for c in hip_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                    r_col = next((c for c in hip_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                    dir_col = next((c for c in hip_ath.columns if "direction" in c.lower() or "test" in c.lower()), None)
                    hip_ad = hip_ath[hip_ath[dir_col].astype(str).str.contains("AD|Adduction", case=False, na=False)] if dir_col else hip_ath
                    hip_ab = hip_ath[hip_ath[dir_col].astype(str).str.contains("AB|Abduction", case=False, na=False)] if dir_col else hip_ath

                    (ad_maxL, ad_maxR), (ad_recL, ad_recR), (ad_initL, ad_initR) = get_peak_and_recent_row(hip_ad, l_col, r_col)
                    (ab_maxL, ab_maxR), (ab_recL, ab_recR), (ab_initL, ab_initR) = get_peak_and_recent_row(hip_ab, l_col, r_col)
                    date_str = format_date_clean(hip_ath.sort_values("Date").iloc[-1].get("Date")) if not hip_ath.empty else "N/A"

                    st.markdown(
                        f"""
                        <div class="hud-metric-row-light-blue">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">2</span>HIP ADDUCTION & ABDUCTION</span>
                                <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                            </div>
                            <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                <b>Hip Adduction:</b> Max L {ad_maxL:.1f}N | R {ad_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ad_recL, ad_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(ad_recR, ad_initR, '{:.1f}', 'N')}<br>
                                <b>Hip Abduction:</b> Max L {ab_maxL:.1f}N | R {ab_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ab_recL, ab_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(ab_recR, ab_initR, '{:.1f}', 'N')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if not calf_ath.empty:
                    l_col = next((c for c in calf_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                    r_col = next((c for c in calf_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                    (ank_maxL, ank_maxR), (ank_recL, ank_recR), (ank_initL, ank_initR) = get_peak_and_recent_row(calf_ath, l_col, r_col)
                    date_str = format_date_clean(calf_ath.sort_values("Date").iloc[-1].get("Date")) if not calf_ath.empty else "N/A"

                    st.markdown(
                        f"""
                        <div class="hud-metric-row-light-blue">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">3</span>ANKLE PLANTAR FLEXION</span>
                                <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                            </div>
                            <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                <b>Max Force:</b> L {ank_maxL:.1f}N | R {ank_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(ank_recL, ank_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(ank_recR, ank_initR, '{:.1f}', 'N')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if not nord_ath.empty:
                    l_col = next((c for c in nord_ath.columns if "l max force" in c.lower() or "left max" in c.lower()), None)
                    r_col = next((c for c in nord_ath.columns if "r max force" in c.lower() or "right max" in c.lower()), None)
                    (nord_maxL, nord_maxR), (nord_recL, nord_recR), (nord_initL, nord_initR) = get_peak_and_recent_row(nord_ath, l_col, r_col)
                    date_str = format_date_clean(nord_ath.sort_values("Date").iloc[-1].get("Date")) if not nord_ath.empty else "N/A"

                    st.markdown(
                        f"""
                        <div class="hud-metric-row-light">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-orange">4</span>NORDBORD HAMSTRING</span>
                                <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                            </div>
                            <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                <b>Peak Force:</b> L {nord_maxL:.1f}N | R {nord_maxR:.1f}N &nbsp;→&nbsp; <b>Recent:</b> L {render_val_with_arrow(nord_recL, nord_initL, '{:.1f}', 'N')} | R {render_val_with_arrow(nord_recR, nord_initR, '{:.1f}', 'N')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if not bs_ath.empty:
                    f_c = next((c for c in bs_ath.columns if "peak vertical force" in c.lower() or "force" in c.lower()), None)
                    if f_c:
                        bs_ath["PVF_Calc"] = pd.to_numeric(bs_ath[f_c].astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce").fillna(0.0)
                        peak_bs_val = bs_ath["PVF_Calc"].max()
                        rec_bs_val = bs_ath.sort_values("Date").iloc[-1]["PVF_Calc"]
                        init_bs_val = bs_ath.sort_values("Date").iloc[0]["PVF_Calc"]
                        date_str = format_date_clean(bs_ath.sort_values("Date").iloc[-1].get("Date"))

                        st.markdown(
                            f"""
                            <div class="hud-metric-row-light-blue">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <span style="font-weight:800; font-size:12px; color:#1D1D1F;"><span class="node-badge-blue">5</span>HARNESS BELT SQUAT</span>
                                    <span style="font-size:10px; color:#6E6E73; font-weight:600;">Latest: {date_str}</span>
                                </div>
                                <div style="font-size:11px; line-height:1.4; color:#1D1D1F;">
                                    <b>Peak Vertical Force:</b> Max {peak_bs_val:.1f}N &nbsp;→&nbsp; <b>Recent:</b> {render_val_with_arrow(rec_bs_val, init_bs_val, '{:.1f}', 'N')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"No Intake Assessment records found for {selected_intake_athlete} in {season_label}.")

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.divider()

        st.divider()

        st.divider()

        st.markdown(f"### Intake Assessment Raw Logs for {selected_intake_athlete} ({season_label})")

        def render_clean_log(df_sub, log_name):
            if df_sub.empty:
                st.info(f"No {log_name} records for {selected_intake_athlete} in {season_label}.")
                return
            
            df_display = df_sub.copy()
            
            # Smart rule to merge Test, Position, and Direction into one clean column
            def get_movement(row):
                pos = row.get('Position')
                dir_ = row.get('Direction')
                test = row.get('Test')
                
                has_pos = pd.notna(pos) and str(pos).strip() != ""
                has_dir = pd.notna(dir_) and str(dir_).strip() != ""
                
                if has_pos and has_dir:
                    return f"{pos} - {dir_}"  # e.g., "Hip IR/ER - Supine - Internal"
                elif has_pos:
                    return pos                # e.g., "Hip IR/ER - Supine"
                elif has_dir:
                    return f"{test} - {dir_}" # e.g., "Knee Extension - Left" (if applicable)
                else:
                    return test               # e.g., "Ankle Plantar Flexion"

            df_display['Position'] = df_display.apply(get_movement, axis=1)

            # The exact target columns you requested
            target_cols = [
                "Date", "Position", "L Max Force (N)", "R Max Force (N)", 
                "Max Imbalance", "L Max Ratio", "R Max Ratio"
            ]
            
            # Only select the columns that actually exist to prevent crash errors
            final_cols = [c for c in target_cols if c in df_display.columns]
            
            st.markdown(render_vball_table(df_display[final_cols]), unsafe_allow_html=True)

        # Expanders customized for your Soccer tests
        with st.expander("Ankle Plantar Flexion Log", expanded=False):
            calf_ath = ankle_data[ankle_data["Name"] == selected_intake_athlete].sort_values("Date") if not ankle_data.empty else pd.DataFrame()
            render_clean_log(calf_ath, "Ankle Assessment")

        with st.expander("Knee Extension / Flexion Log", expanded=False):
            sh_ath = knee_data[knee_data["Name"] == selected_intake_athlete].sort_values("Date") if not knee_data.empty else pd.DataFrame()
            render_clean_log(sh_ath, "Knee Assessment")

        with st.expander("Hip AD/AB Log", expanded=False):
            hip_ad_ath = hip_ad_ab_data[hip_ad_ab_data["Name"] == selected_intake_athlete].sort_values("Date") if not hip_ad_ab_data.empty else pd.DataFrame()
            render_clean_log(hip_ad_ath, "Hip AD/AB")

        with st.expander("Hip IR/ER Log", expanded=False):
            hip_ir_ath = hip_ir_er_data[hip_ir_er_data["Name"] == selected_intake_athlete].sort_values("Date") if not hip_ir_er_data.empty else pd.DataFrame()
            render_clean_log(hip_ir_ath, "Hip IR/ER")
            
        with st.expander("Shoulder Log", expanded=False):
            shoulder_ath = shoulder_data[shoulder_data["Name"] == selected_intake_athlete].sort_values("Date") if not shoulder_data.empty else pd.DataFrame()
            render_clean_log(shoulder_ath, "Shoulder")

    # SECTION 5B: CMJ TAB
    with testing_tab_cmj:
        st.markdown(
            f'<div class="vball-section-title">CMJ Performance Standards & History — {season_label}</div>',
            unsafe_allow_html=True,
        )

        c_filter, c_cmj_dt = st.columns(2)
        with c_filter:
            selected_player_t = st.selectbox(
                "Select Athlete:", roster_players, key=f"cmj_player_select_{season_key}"
            )

        ath_all_jumps = (
            cmj_raw[cmj_raw["Name"] == selected_player_t].sort_values("Date")
            if not cmj_raw.empty and "Name" in cmj_raw.columns
            else pd.DataFrame()
        )
        avail_cmj_dates = ath_all_jumps["Date_Str"].dropna().unique().tolist()[::-1] if not ath_all_jumps.empty else []

        with c_cmj_dt:
            selected_cmj_test_date = st.selectbox(
                "Select CMJ Test Date:",
                options=avail_cmj_dates if avail_cmj_dates else ["No jumps recorded"],
                format_func=format_date_clean,
                key=f"cmj_test_top_date_sel_{season_key}",
            )

        render_cmj_tscore_standards(
            selected_player_t,
            cmj_raw,
            target_date_str=selected_cmj_test_date,
            widget_key_suffix=f"testing_{season_key}"
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

            display_cols = [
                c for c in p_cmj.columns if c not in ["Name", "Date_Str", "Jump_Height_Clean", "RSI_Clean"]
            ]
            stiffness_col = next((c for c in display_cols if "stiffness" in c.lower()), None)
            if stiffness_col:
                end_idx = display_cols.index(stiffness_col) + 1
                display_cols = display_cols[:end_idx]

            st.markdown(f"### Jump History Logs for {selected_player_t} ({season_label})")
            st.markdown(render_vball_table(p_cmj[display_cols]), unsafe_allow_html=True)
        else:
            st.info(f"No Countermovement Jump (CMJ) logs found for {selected_player_t} in {season_label}.")

    # SECTION 5C: OVERALL PROFILE
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

        p_bs_ov = belt_squat_data[belt_squat_data["Name"] == selected_ov_athlete] if not belt_squat_data.empty and "Name" in belt_squat_data.columns else pd.DataFrame()
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
