import streamlit as st
import pandas as pd
import json
from supabase import create_client

# --- Supabase Setup ---
SUPABASE_URL = "https://sdeqwebuathtwfugdvvr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkZXF3ZWJ1YXRodHdmdWdkdnZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ5MjQ5MjcsImV4cCI6MjA1MDUwMDkyN30.asWjo-qcD0Dzi36rGLLLFzwzSPB3Y_JScc1RswxIGig"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Supabase Functions ---
def save_sheep_info(data):
    """Save or update sheep information in Supabase."""
    response = supabase.table("sheep").upsert(data).execute()
    if response.get("error"):
        st.error(response["error"]["message"])

def save_activity_info(data):
    """Save activity details for a sheep."""
    response = supabase.table("activities").insert(data).execute()
    if response.get("error"):
        st.error(response["error"]["message"])

def fetch_sheep_with_activities():
    """Fetch all sheep and their activities from Supabase."""
    response = supabase.rpc("get_sheep_with_activities").execute()  # Assuming a custom RPC function
    if response.get("error"):
        st.error(response["error"]["message"])
    else:
        return pd.DataFrame(response["data"])

def fetch_single_sheep(sheep_id):
    """Fetch a single sheep record for editing."""
    response = supabase.table("sheep").select("*").eq("sheep_id", sheep_id).execute()
    if response.get("error"):
        st.error(response["error"]["message"])
    else:
        return response.get("data", [{}])[0]

# --- Streamlit App UI ---
st.title("\U0001F411 Sheep Management System")

# Collect Basic Information
st.header("Enter Sheep Details")
sheep_id = st.text_input("Sheep ID", placeholder="Enter or select a Sheep ID to edit")
if st.button("Load Record") and sheep_id:
    sheep_record = fetch_single_sheep(sheep_id)
    if sheep_record:
        st.session_state["purchased_date"] = sheep_record.get("purchased_date")
        st.session_state["sex"] = sheep_record.get("sex")
        st.session_state["pregnant"] = sheep_record.get("pregnant")
        st.session_state["weight"] = sheep_record.get("weight")
        st.session_state["body_score"] = sheep_record.get("body_score")
        st.session_state["age"] = sheep_record.get("age")
        st.session_state["notes"] = sheep_record.get("notes")

sheep_data = {
    "sheep_id": sheep_id,
    "purchased_date": st.date_input("Date of Birth/Purchase", value=st.session_state.get("purchased_date")),
    "sex": st.selectbox("Sex", ["Male", "Female"], index=["Male", "Female"].index(st.session_state.get("sex", "Male"))),
    "pregnant": st.checkbox("Is Pregnant?", value=st.session_state.get("pregnant", False)),
    "weight": st.number_input("Weight (kg)", min_value=0.0, step=0.1, value=st.session_state.get("weight", 0.0)),
    "body_score": st.slider("Body Score (1-5)", 1, 5, value=st.session_state.get("body_score", 3)),
    "age": st.number_input("Approx Age (in years)", min_value=0, step=1, value=st.session_state.get("age", 0)),
    "notes": st.text_area("Notes", value=st.session_state.get("notes", "")),
}

# Select Activity
activity = st.selectbox("Activity", ["Vaccination", "Lambing", "Culling", "Sale"])
activity_details = {}

if activity == "Vaccination":
    st.subheader("Vaccination Details")
    vaccination_type = st.text_input("Vaccination Type")
    dose_sequence = st.text_input("Dose Sequence")
    notes = st.text_area("Additional Notes")
    activity_details = {
        "vaccination_type": vaccination_type,
        "dose_sequence": dose_sequence,
        "notes": notes,
    }

elif activity == "Lambing":
    st.subheader("Lambing Details")
    lambing_number = st.number_input("Lambing Number", min_value=1, step=1)
    num_babies = st.number_input("Number of Babies Born", min_value=0, step=1)
    babies = []
    for i in range(int(num_babies)):
        baby_sex = st.selectbox(f"Sex of Baby {i+1}", ["Male", "Female"], key=f"baby_sex_{i}")
        baby_weight = st.number_input(f"Weight of Baby {i+1} (kg)", min_value=0.0, step=0.1, key=f"baby_weight_{i}")
        babies.append({"sex": baby_sex, "weight": baby_weight})
    activity_details = {
        "lambing_number": lambing_number,
        "num_babies": num_babies,
        "babies": babies,
    }

elif activity == "Culling":
    st.subheader("Culling Details")
    culling_date = st.date_input("Culling Date")
    reason = st.text_area("Reason for Culling")
    activity_details = {
        "date": str(culling_date),
        "reason": reason,
    }

elif activity == "Sale":
    st.subheader("Sale Details")
    sale_date = st.date_input("Sale Date")
    buyer_name = st.text_input("Buyer Name")
    sale_price = st.number_input("Sale Price (PKR)", min_value=0.0, step=0.1)
    activity_details = {
        "sale_date": str(sale_date),
        "buyer_name": buyer_name,
        "sale_price": sale_price,
    }

# Submit Button
if st.button("Save Record"):
    # Save basic sheep info
    save_sheep_info(sheep_data)

    # Save activity info
    save_activity_info({"sheep_id": sheep_data["sheep_id"], "activity": activity, "details": activity_details})
    st.success("Record saved successfully!")

# Display Records
st.header("\U0001F4CB View All Records")
if st.button("Show Records"):
    df = fetch_sheep_with_activities()
    if df.empty:
        st.warning("No records found.")
    else:
        st.dataframe(df)

if st.button("Export to CSV"):
    df = fetch_sheep_with_activities()
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="sheep_data.csv",
            mime="text/csv",
        )
        st.success("Data is ready for download.")
    else:
        st.warning("No data to export.")
