import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import graphviz
import json
import os

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Org Chart Visualizer", page_icon="📊", layout="centered")

st.title("📊 Org Chart Visualizer")
st.caption("Easily visualize organizational hierarchies from Google Sheets or LibreOffice files.")

# ---- ROLE PRESET UTILS ----
def save_role_map(role_map):
    with open("role_presets.json", "w") as f:
        json.dump(role_map, f)

def load_role_map():
    if os.path.exists("role_presets.json"):
        with open("role_presets.json", "r") as f:
            return json.load(f)
    return {}

# ---- SHEET READERS ----
def read_google_sheet(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # ✅ Load credentials from Streamlit Secrets (safe!)
    import json
    creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
    creds =  ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def read_ods(file):
    return pd.read_excel(file, engine="odf")

# ---- SECTION 1: Upload ----
st.header("1️⃣ Upload Your Org Sheet")
source = st.radio("Select Source:", ["Google Sheet", "Upload LibreOffice Sheet (.ods)"])

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
    st.subheader("📄 Preview of Uploaded Data")
    st.dataframe(df)

    if "Name" not in df.columns or "Role" not in df.columns:
        st.warning("⚠️ Sheet must contain 'Name' and 'Role' columns.")
    else:
        st.header("2️⃣ Rename or Standardize Roles (Optional)")

        role_map = load_role_map()
        new_role_map = {}

        for role in df["Role"].unique():
            new_name = st.text_input(f"Rename '{role}' to:", value=role_map.get(role, role))
            new_role_map[role] = new_name

        if st.button("💾 Save Presets"):
            save_role_map(new_role_map)
            st.success("✅ Presets saved!")

        df["Role"] = df["Role"].map(new_role_map)

        # ---- SECTION 3: Visualize Org Chart ----
        st.header("3️⃣ Visualize Hierarchy")

        def draw_hierarchy(df):
            dot = graphviz.Digraph(format="png")
            sorted_df = df.sort_values(by="Role")

            for _, row in sorted_df.iterrows():
                dot.node(row["Name"], f'{row["Name"]}\n({row["Role"]})')

            for i in range(1, len(sorted_df)):
                dot.edge(sorted_df.iloc[i - 1]["Name"], sorted_df.iloc[i]["Name"])

            dot.render("org_chart", cleanup=True)
            return dot

        dot = draw_hierarchy(df)
        st.graphviz_chart(dot)

        # ---- DOWNLOAD CHART BUTTON ----
        with open("org_chart.png", "rb") as f:
            st.download_button(
                label="📥 Download Org Chart as PNG",
                data=f,
                file_name="org_chart.png",
                mime="image/png"
            )

        st.success("✅ Org chart generated!")



