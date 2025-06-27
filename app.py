import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import graphviz
import json
import os

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Org Chart Visualizer", page_icon="🧱", layout="wide")

# ---- NEO-BRUTALIST HEADER & STYLE ----
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');

        html, body, .stApp {
            background-color: #fdfdfd;
            color: #000000;
            font-family: 'Space Mono', monospace;
        }

        .main-title {
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            background-color: #000;
            color: #fff;
            padding: 15px;
            border: 4px solid #000;
            box-shadow: 5px 5px 0 #ff00aa;
            margin: 20px;
        }

        .block-style {
            border: 3px solid #000;
            background-color: #ffff00;
            padding: 10px;
            margin: 20px 0;
            box-shadow: 4px 4px 0 #000;
        }

        .stButton>button, .stTextInput>div>input {
            border: 3px solid #000 !important;
            box-shadow: 3px 3px 0 #000 !important;
            font-family: 'Space Mono', monospace;
        }

        .fab-button {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #000;
            color: #fff;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 28px;
            text-align: center;
            line-height: 60px;
            box-shadow: 5px 5px 0 #ff00aa;
            cursor: pointer;
            z-index: 100;
        }
    </style>
    <div class='main-title'>🧱 Org Chart Visualizer</div>
    <a href='#top'>
        <div class='fab-button'>↑</div>
    </a>
""", unsafe_allow_html=True)

st.caption("Visualize your organization in brutal clarity.")

# ---- UTILS ----
def save_role_map(role_map):
    with open("role_presets.json", "w") as f:
        json.dump(role_map, f)

def load_role_map():
    if os.path.exists("role_presets.json"):
        with open("role_presets.json", "r") as f:
            return json.load(f)
    return {}

def read_google_sheet(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def read_ods(file):
    return pd.read_excel(file, engine="odf")

# ---- SIDEBAR INPUT ----
st.sidebar.header("📁 Upload Options")
source = st.sidebar.radio("Select Source", ["Google Sheet", "LibreOffice (.ods)"])

# ---- SECTION 1: Upload ----
st.markdown("## 📤 Step 1: Upload Your Org Sheet", unsafe_allow_html=True)

with st.container():
    df = None
    if source == "Google Sheet":
        sheet_url = st.text_input("Paste your Google Sheet URL:")
        if sheet_url:
            try:
                df = read_google_sheet(sheet_url)
                st.success("✅ Google Sheet loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error loading sheet: {e}")
    else:
        uploaded_file = st.file_uploader("Upload LibreOffice (.ods) file:", type=["ods"])
        if uploaded_file:
            try:
                df = read_ods(uploaded_file)
                st.success("✅ LibreOffice file uploaded successfully!")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# ---- SECTION 2: Rename Roles ----
if df is not None:
    st.markdown("## ✏️ Step 2: Rename or Standardize Roles", unsafe_allow_html=True)
    st.dataframe(df)

    if "Name" not in df.columns or "Role" not in df.columns:
        st.warning("⚠️ Sheet must contain 'Name' and 'Role' columns.")
    else:
        role_map = load_role_map()
        new_role_map = {}

        with st.expander("🛠️ Customize Roles"):
            for role in df["Role"].unique():
                new_name = st.text_input(f"Rename '{role}' to:", value=role_map.get(role, role))
                new_role_map[role] = new_name

        if st.button("💾 Save Presets"):
            save_role_map(new_role_map)
            st.success("✅ Presets saved!")

        df["Role"] = df["Role"].map(new_role_map)

        # ---- SECTION 3: Visualize Org Chart ----
        with st.expander("📈 Step 3: Visualize Org Chart", expanded=True):
            def draw_hierarchy(df):
                dot = graphviz.Digraph()
                sorted_df = df.sort_values(by="Role")
                for _, row in sorted_df.iterrows():
                    dot.node(row["Name"], f'{row["Name"]}\n({row["Role"]})')
                for i in range(1, len(sorted_df)):
                    dot.edge(sorted_df.iloc[i - 1]["Name"], sorted_df.iloc[i]["Name"])
                return dot

            dot = draw_hierarchy(df)
            st.graphviz_chart(dot)
            st.toast("✅ Org chart is ready!", icon="💼")









