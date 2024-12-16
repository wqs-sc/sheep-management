import sqlite3
import streamlit as st
import pandas as pd
import json


# --- Database Setup ---
def connect_db():
    conn = sqlite3.connect("sheep_management.db")
    return conn


def setup_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Sheep table for basic information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sheep (
            tag_id TEXT PRIMARY KEY,
            dob_purchase TEXT,
            sex TEXT,
            approx_age INTEGER,
            weight REAL,
            body_score INTEGER,
            feed_type TEXT
        )
    ''')

    # Activities table for storing multiple activities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id TEXT,
            activity TEXT,
            details TEXT,
            FOREIGN KEY(tag_id) REFERENCES sheep(tag_id)
        )
    ''')
    conn.commit()
    conn.close()


# --- Database Functions ---
def save_sheep_info(data):
    """Save or update basic sheep information."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO sheep (tag_id, dob_purchase, sex, approx_age, weight, body_score, feed_type)
        VALUES (:tag_id, :dob_purchase, :sex, :approx_age, :weight, :body_score, :feed_type)
        ON CONFLICT(tag_id) DO UPDATE SET 
            dob_purchase=:dob_purchase, sex=:sex, approx_age=:approx_age, weight=:weight,
            body_score=:body_score, feed_type=:feed_type
    ''', data)
    conn.commit()
    conn.close()


def save_activity_info(tag_id, activity, details):
    """Save activity details for a sheep."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO activities (tag_id, activity, details)
        VALUES (?, ?, ?)
    ''', (tag_id, activity, json.dumps(details)))
    conn.commit()
    conn.close()


def fetch_sheep_with_activities():
    """Fetch all sheep and their activities."""
    conn = connect_db()
    query = '''
        SELECT s.tag_id, s.dob_purchase, s.sex, s.approx_age, s.weight, s.body_score, s.feed_type,
               a.activity, a.details
        FROM sheep s
        LEFT JOIN activities a ON s.tag_id = a.tag_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# --- Streamlit App UI ---
setup_database()
st.title("🐑 Sheep Management System")

# Collect Basic Information
st.header("Enter Sheep Details")
tag_id = st.text_input("Tag ID", placeholder="Enter a unique Tag ID")
dob_purchase = st.date_input("Date of Birth/Purchase")
sex = st.selectbox("Sex", ["Male", "Female"])
approx_age = st.number_input("Approx Age (in months)", min_value=0, step=1)
weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
body_score = st.slider("Body Score (1-5)", 1, 5)
feed_type = st.selectbox("Feed in Last 20 Days", ["Pasture", "Grain", "Both"])

# Select Activity
activity = st.selectbox("Activity",
                        ["Vaccination", "Lambing", "Culling", "Sale"])

# Activity-Specific Inputs
activity_details = {}

if activity == "Vaccination":
    st.subheader("Vaccination Details")
    for v in ["A", "B", "C", "D"]:
        st.write(f"**Vaccination {v}**")
        dose1 = st.date_input(f"1st Dose Date ({v})", key=f"{v}_dose1")
        dose2 = st.date_input(f"2nd Dose Date ({v})", key=f"{v}_dose2")
        dose3 = st.date_input(f"3rd Dose Date ({v})", key=f"{v}_dose3")
        dose4 = st.date_input(f"4th Dose Date ({v})", key=f"{v}_dose4")
        dose5 = st.date_input(f"5th Dose Date ({v})", key=f"{v}_dose5")
        activity_details[v] = {
            "dose1": str(dose1) if dose1 else "",
            "dose2": str(dose2) if dose2 else "",
            "dose3": str(dose3) if dose3 else "",
            "dose4": str(dose4) if dose4 else "",
            "dose5": str(dose5) if dose5 else ""
        }

elif activity == "Lambing":
    st.subheader("Lambing Details")
    lambing_number = st.selectbox("Lambing Number", [1, 2, 3])
    babies_born = st.number_input("Babies Born", min_value=0, step=1)
    baby_details = []
    for i in range(int(babies_born)):
        st.subheader(f"Baby {i+1}")
        baby_sex = st.selectbox(f"Sex of Baby {i+1}", ["Male", "Female"],
                                key=f"baby_sex_{i}")
        baby_dob = st.date_input(f"DOB of Baby {i+1}", key=f"baby_dob_{i}")
        baby_details.append({"sex": baby_sex, "dob": str(baby_dob)})
    activity_details = {
        "lambing_number": lambing_number,
        "babies": baby_details
    }

elif activity == "Culling":
    st.subheader("Culling Details")
    culling_reason = st.text_area("Reason for Culling")
    culling_date = st.date_input("Culling Date")
    activity_details = {
        "reason": culling_reason,
        "date": str(culling_date) if culling_date else ""
    }

elif activity == "Sale":
    st.subheader("Sale Details")
    sale_date = st.date_input("Sale Date")
    sale_weight = st.number_input("Sale Weight (kg)", min_value=0.0)
    sale_price = st.number_input("Sale Price (PKR)", min_value=0.0)
    activity_details = {
        "sale_date": str(sale_date),
        "sale_weight": sale_weight,
        "sale_price": sale_price
    }

# Submit Button
if st.button("Save Record"):
    if not tag_id.strip():
        st.error("Tag ID is required!")
    else:
        # Save basic sheep info
        sheep_data = {
            "tag_id": tag_id,
            "dob_purchase": str(dob_purchase),
            "sex": sex,
            "approx_age": int(approx_age),
            "weight": float(weight),
            "body_score": int(body_score),
            "feed_type": feed_type
        }
        save_sheep_info(sheep_data)

        # Save activity info
        save_activity_info(tag_id, activity, activity_details)
        st.success("Record saved successfully!")

# Display Records
st.header("📋 View All Records")
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
