import streamlit as st
import pandas as pd

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

# Team Filter
teams = df_roster['Sport'].dropna().unique().tolist()
selected_team = st.sidebar.selectbox("Select Team", ["All Teams"] + teams)

# Player Filter (dependent on Team)
if selected_team != "All Teams":
    filtered_roster = df_roster[df_roster['Sport'] == selected_team]
else:
    filtered_roster = df_roster

players = filtered_roster['Name'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select Player", ["All Players"] + players)

# Filter the ForceFrame Data based on selections
filtered_ff = df_forceframe.copy()
if selected_team != "All Teams":
    filtered_ff = filtered_ff[filtered_ff['Sport'] == selected_team]
if selected_player != "All Players":
    filtered_ff = filtered_ff[filtered_ff['Name'] == selected_player]

# ==========================================
# 4. TABS FOR THE 5 SHEETS
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "ForceFrame", 
    "Roster", 
    "Sheet 3 (Hidden)", 
    "Sheet 4 (Hidden)", 
    "Sheet 5 (Hidden)"
])

with tab1:
    st.subheader(f"ForceFrame Data: {selected_player}")
    
    # Example: Display Key Performance Indicators (KPIs) if a single player is selected
    if selected_player != "All Players" and not filtered_ff.empty:
        col1, col2, col3 = st.columns(3)
        latest_test = filtered_ff.iloc[0] # Assumes sorted by date
        col1.metric("Latest L Max Force (N)", f"{latest_test['L Max Force (N)']}")
        col2.metric("Latest R Max Force (N)", f"{latest_test['R Max Force (N)']}")
        col3.metric("Max Imbalance", f"{latest_test['Max Imbalance']}")
        st.markdown("<br>", unsafe_allow_html=True)
        
    st.dataframe(filtered_ff, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Team Roster")
    st.dataframe(filtered_roster, use_container_width=True, hide_index=True)

with tab3:
    st.info("Load your 3rd secret sheet here.")

with tab4:
    st.info("Load your 4th secret sheet here.")
    
with tab5:
    st.info("Load your 5th secret sheet here.")
