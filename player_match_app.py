
import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from datetime import datetime

st.set_page_config(page_title="Identity Circumvention Detection", layout="wide")
st.title("🎰 Identity Circumvention Detection Tool")

uploaded_file = st.file_uploader("Upload New Player File (.csv or .xlsx)", type=["csv", "xlsx"])

@st.cache_data
def load_database():
    try:
        return pd.read_csv("player_database.csv", dtype=str, parse_dates=["DOB"])
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "First Name", "Last Name", "Postcode", "DOB", "Mobile", "Email",
            "Casino", "Network ID", "Player ID"
        ])

existing = load_database()

def parse_dob(dob):
    try:
        return pd.to_datetime(dob, errors='coerce')
    except:
        return None

def dob_close(d1, d2):
    if pd.isna(d1) or pd.isna(d2):
        return False
    return (
        abs((d1 - d2).days) <= 1 or
        (d1.month == d2.month and d1.day == d2.day and abs(d1.year - d2.year) == 1) or
        (d1.year == d2.year and d1.day == d2.day and abs(d1.month - d2.month) == 1)
    )

if uploaded_file:
    new = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    new["DOB"] = new["DOB"].apply(parse_dob)
    existing["DOB"] = existing["DOB"].apply(parse_dob)

    matches = []

    for _, n in new.iterrows():
        for _, e in existing.iterrows():
            if n["Casino"].strip().lower() != e["Casino"].strip().lower():
                continue

            fn_sim = fuzz.ratio(str(n["First Name"]).lower(), str(e["First Name"]).lower())
            ln_sim = fuzz.ratio(str(n["Last Name"]).lower(), str(e["Last Name"]).lower())
            name_exact = fn_sim == 100 and ln_sim == 100
            name_altered = fn_sim < 100 or ln_sim < 100

            dob_exact = n["DOB"] == e["DOB"]
            dob_near = dob_close(n["DOB"], e["DOB"])

            if name_altered and dob_exact:
                matches.append({
                    "New Player ID": n["Player ID"],
                    "Existing Player ID": e["Player ID"],
                    "Casino": n["Casino"],
                    "Match Rule": "Altered name + Exact DOB"
                })
            elif name_exact and dob_near:
                matches.append({
                    "New Player ID": n["Player ID"],
                    "Existing Player ID": e["Player ID"],
                    "Casino": n["Casino"],
                    "Match Rule": "Same name + Near DOB"
                })
            elif name_altered and dob_near:
                matches.append({
                    "New Player ID": n["Player ID"],
                    "Existing Player ID": e["Player ID"],
                    "Casino": n["Casino"],
                    "Match Rule": "Altered name + Near DOB"
                })

    st.subheader("🔍 Possible Circumvention Matches")
    if matches:
        result_df = pd.DataFrame(matches)
        st.dataframe(result_df)
        st.success(f"{len(matches)} potential match(es) found.")

        if st.button("📥 Add new players to database"):
            full_db = pd.concat([existing, new], ignore_index=True)
            full_db.to_csv("player_database.csv", index=False)
            st.success("Database updated with new players.")
    else:
        st.info("No suspicious circumvention patterns detected.")
else:
    st.info("Please upload a file to start matching.")
