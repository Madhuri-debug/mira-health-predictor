import streamlit as st
import sqlite3
import re
from datetime import date

# 1. డేటాబేస్ కనెక్షన్
conn = sqlite3.connect('healthcare.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, dob TEXT, email TEXT,
        glucose REAL, hemoglobin REAL, cholesterol REAL, remarks TEXT
    )
''')
conn.commit()

# 2. AI/ML ప్రెడిక్షన్ లాజిక్
def predict_health_risk(glucose, hb, choles):
    risks = []
    if glucose > 140: risks.append("High Blood Sugar (Risk of Diabetes)")
    elif glucose < 70: risks.append("Low Blood Sugar (Hypoglycemia)")
    if hb < 12.0: risks.append("Low Hemoglobin (Risk of Anemia)")
    if choles > 200: risks.append("High Cholesterol (Risk of Cardiovascular issues)")
    
    if not risks:
        return "All parameters look stable. Maintain a healthy lifestyle."
    return "Potential Risks: " + ", ".join(risks)

# 3. Streamlit UI
st.set_page_config(page_title="MIRA Health Predictor", layout="wide")
st.title("🏥 MIRA - Health Prediction Application")

menu = ["Add Patient Record", "View & Manage Records"]
choice = st.sidebar.selectbox("Menu", menu)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ================= ADD RECORD =================
if choice == "Add Patient Record":
    st.subheader("📝 Enter Patient Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        dob = st.date_input("Date of Birth", max_value=date.today())
        email = st.text_input("Email Address")
    with col2:
        glucose = st.number_input("Glucose (mg/dL)", min_value=0.0, step=1.0)
        hemoglobin = st.number_input("Hemoglobin (g/dL)", min_value=0.0, step=0.1)
        cholesterol = st.number_input("Cholesterol (mg/dL)", min_value=0.0, step=1.0)

    if st.button("Submit & Predict Health Status"):
        if not name or not email:
            st.error("Please fill all personal details.")
        elif not is_valid_email(email):
            st.error("Invalid Email Format!")
        else:
            remarks = predict_health_risk(glucose, hemoglobin, cholesterol)
            c.execute('''
                INSERT INTO patients (name, dob, email, glucose, hemoglobin, cholesterol, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, str(dob), email, glucose, hemoglobin, cholesterol, remarks))
            conn.commit()
            st.success(f"Record successfully saved for {name}!")
            st.info(f"🧬 AI Remarks: {remarks}")

# ================= VIEW & MANAGE (CRUD) =================
elif choice == "View & Manage Records":
    st.subheader("🔍 Patient Database & Analytics")
    c.execute("SELECT * FROM patients")
    data = c.fetchall()
    
    if not data:
        st.warning("No records found.")
    else:
        for row in data:
            with st.expander(f"Patient: {row[1]} (ID: {row[0]})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**DOB:** {row[2]}")
                    st.write(f"**Email:** {row[3]}")
                    st.write(f"**AI Remarks:** `{row[7]}`")
                with col2:
                    new_glucose = st.number_input(f"Edit Glucose", value=row[4], key=f"g_{row[0]}")
                    new_hb = st.number_input(f"Edit Hemoglobin", value=row[5], key=f"h_{row[0]}")
                    new_ch = st.number_input(f"Edit Cholesterol", value=row[6], key=f"c_{row[0]}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("🔄 Update", key=f"up_{row[0]}"):
                        new_remarks = predict_health_risk(new_glucose, new_hb, new_ch)
                        c.execute('''
                            UPDATE patients 
                            SET glucose=?, hemoglobin=?, cholesterol=?, remarks=? 
                            WHERE id=?
                        ''', (new_glucose, new_hb, new_ch, new_remarks, row[0]))
                        conn.commit()
                        st.success("Updated!")
                        st.rerun()
                        
                    if c2.button("🗑️ Delete", key=f"del_{row[0]}"):
                        c.execute("DELETE FROM patients WHERE id=?", (row[0],))
                        conn.commit()
                        st.error("Deleted!")
                        st.rerun()
