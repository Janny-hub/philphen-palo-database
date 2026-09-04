import datetime
import sqlite3
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("philpen_palo.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_date TEXT,
            last_name TEXT,
            first_name TEXT,
            middle_name TEXT,
            zone TEXT,
            barangay TEXT,
            birthday TEXT,
            age INTEGER,
            sex TEXT,
            weight_kg REAL,
            height_cm REAL,
            bmi REAL,
            bmi_class TEXT,
            waist_cm REAL,
            waist_risk TEXT,
            has_diabetes TEXT,
            diabetes_meds TEXT,
            has_hypertension TEXT,
            hypertension_meds TEXT,
            high_cholesterol TEXT,
            history_cvd_stroke INTEGER,
            history_heart_attack INTEGER,
            history_kidney INTEGER,
            family_history TEXT,
            bp_1 TEXT,
            bp_2 TEXT,
            bp_3 TEXT,
            bp_avg TEXT,
            is_smoker TEXT,
            is_binge_drinker TEXT,
            is_exercising TEXT,
            eats_healthy TEXT,
            risk_level TEXT,
            action_taken TEXT,
            bhw_name TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()

# ---------------------------------------------------------
# BARANGAY CREDENTIALS
# ---------------------------------------------------------
BARANGAY_CREDENTIALS = {
    "Anahaway": "anah123",
    "Arado": "arad123",
    "Baras": "bara123",
    "Barayong": "bary123",
    "Cabarasan Daku": "cabd123",
    "Cabarasan Guti": "cabg123",
    "Campetic": "camp123",
    "Candahug": "cand123",
    "Cangumbang": "cang123",
    "Canhidoc": "canh123",
    "Capirawan": "capi123",
    "Castilla": "cast123",
    "Cogon": "cogo123",
    "San Joaquin": "joaq123",
    "Gacao": "gaca123",
    "Guindapunan": "guin123",
    "Libertad": "libe123",
    "Naga-naga": "naga123",
    "Pawing": "pawi123",
    "Buri (Poblacion barangay)": "buri123",
    "Cavite East (Pob. barangay)": "cave123",
    "Cavite West (Poblacion)": "cavw123",
    "Luntad (Poblacion)": "lunt123",
    "Santa Cruz (Poblacion)": "sant123",
    "Salvacion": "salv123",
    "San Agustin": "agust123",
    "San Antonio": "anto123",
    "San Isidro": "isid123",
    "San Jose": "jose123",
    "St. Michael (Poblacion)": "mich123",
    "Tacuranga": "tacu123",
    "Teraza": "tera123",
    "San Fernando": "fern123",
}

# ---------------------------------------------------------
# COMPUTATION HELPER FUNCTIONS
# ---------------------------------------------------------
def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def calculate_bmi(weight, height):
    if height > 0:
        return round((weight / height / height) * 10000, 2)
    return 0.0


def classify_bmi(bmi):
    if bmi < 18.5:
        return "< 18.5 (UNDERWEIGHT)"
    elif 18.5 <= bmi <= 22.9:
        return "18.5 - 22.9 (NORMAL)"
    elif 23.0 <= bmi <= 24.9:
        return "23.0 - 24.9 (OVERWEIGHT OR AT RISK)"
    else:
        return "25.0 or more (OBESITY)"


def classify_waist(sex, waist):
    if sex == "Male":
        return "AT RISK (≥ 90 cm)" if waist >= 90 else "NOT AT RISK (< 90 cm)"
    elif sex == "Female":
        return "AT RISK (≥ 80 cm)" if waist >= 80 else "NOT AT RISK (< 80 cm)"
    return "N/A"


def calculate_cvd_risk(age, sex, smoker, sbp, bmi, diabetes):
    if diabetes == "Meron" or sbp >= 160 or bmi >= 25.0:
        if age >= 60 or sbp >= 160:
            return "High", "20% to <30%"
        return "Medium", "10% to <20%"
    elif smoker == "Oo" or sbp >= 140:
        return "Mild", "5% to <10%"
    return "Low", "<5%"


# ---------------------------------------------------------
# STREAMLIT CONFIG & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Palo Community Health System", layout="wide"
)

st.markdown(
    """
    <style>
    /* Main App Background */
    .stApp {
        background-color: #f4f6f8;
    }
    
    /* Header Banner Styling */
    .header-container {
        background: linear-gradient(90deg, #d90429 0%, #ffb703 100%);
        padding: 22px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }
    .header-container h1 {
        color: #ffffff !important;
        margin: 0;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .header-container p {
        color: #fff3bf;
        margin: 6px 0 0 0;
        font-size: 1.1rem;
    }

    /* Card Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Display
st.markdown(
    """
    <div class="header-container">
        <h1>Community Health Information System</h1>
        <p>Rural Health Unit — Municipality of Palo, Leyte</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""

if not st.session_state["authenticated"]:
    st.subheader("Barangay Portal Login")
    with st.form("login_form"):
        username = st.selectbox("Select Barangay Username", list(BARANGAY_CREDENTIALS.keys()))
        password = st.text_input("Barangay Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if BARANGAY_CREDENTIALS.get(username) == password:
                st.session_state["authenticated"] = True
                st.session_state["user_brgy"] = username
                st.rerun()
            else:
                st.error("Incorrect password for the selected Barangay.")
    st.stop()

# ---------------------------------------------------------
# NAVIGATION & SIDEBAR
# ---------------------------------------------------------
st.sidebar.title(f"📍 Brgy. {st.session_state['user_brgy']}")
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Program Modules",
    [
        "📊 Dashboard Overview",
        "📋 PhilPEN Risk Assessment",
        "📈 PhilPEN Data Analytics",
        "👶 Nutritional Status (0-59 mos)",
        "💉 Immunization (EPI)",
        "🤰 Maternal Care",
        "🐌 Schistosomiasis Program",
        "🫁 National TB Program (NTP)",
    ],
)

# ---------------------------------------------------------
# MODULE 1: DASHBOARD OVERVIEW
# ---------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.subheader(f"Welcome, Health Workers of Brgy. {st.session_state['user_brgy']}!")
    st.info("Select a program module from the sidebar menu to input data, review health records, or generate analytical reports.")

    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query("SELECT * FROM assessments WHERE barangay = ?", conn, params=(st.session_state["user_brgy"],))
    conn.close()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total PhilPEN Screened", len(df))
    m2.metric("Adults (20-64 yrs)", len(df[(df['age'] >= 20) & (df['age'] <= 64)]))
    m3.metric("Seniors (65+ yrs)", len(df[df['age'] >= 65]))

# ---------------------------------------------------------
# MODULE 2: PHILPEN RISK ASSESSMENT FORM
# ---------------------------------------------------------
elif menu == "📋 PhilPEN Risk Assessment":
    st.subheader(f"PhilPEN Risk Assessment Form — Brgy. {st.session_state['user_brgy']}")

    with st.form("assessment_form"):
        st.write("**1. General Information**")
        col1, col2, col3 = st.columns(3)
        with col1:
            assessment_date = st.date_input("Date of Assessment*", datetime.date.today())
            last_name = st.text_input("Apilido (Last Name)*")
        with col2:
            first_name = st.text_input("Pangalan (Given Name)*")
            middle_name = st.text_input("Gitnang Pangalan (Middle Name)")
        with col3:
            zone = st.text_input("Zone / Purok*")
            barangay = st.text_input("Barangay", value=st.session_state["user_brgy"], disabled=True)

        col_dob, col_sex = st.columns(2)
        with col_dob:
            dob = st.date_input(
                "Birthday*",
                min_value=datetime.date(1920, 1, 1),
                max_value=datetime.date.today(),
            )
            age = calculate_age(dob)
            st.info(f"**Calculated Age:** {age} years old")
        with col_sex:
            sex = st.radio("Sex*", ["Male", "Female", "Other"])

        st.write("**2. Body Measurements & Auto-Calculations**")
        col_w, col_h = st.columns(2)
        with col_w:
            weight = st.number_input("Timbang / Weight (kg)*", min_value=1.0, max_value=300.0, step=0.5)
        with col_h:
            height = st.number_input("Taas / Height (cm)*", min_value=30.0, max_value=250.0, step=0.5)

        bmi = calculate_bmi(weight, height)
        bmi_cat = classify_bmi(bmi)
        st.success(f"**Calculated BMI:** {bmi} | **Classification:** {bmi_cat}")

        waist = st.number_input("Waist Circumference (cm)*", min_value=20.0, max_value=200.0, step=0.5)
        waist_risk = classify_waist(sex, waist)
        st.info(f"**Waist Risk Status:** {waist_risk}")

        st.write("**3. Medical History**")
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"])
        diabetes_meds = st.selectbox(
            "Ano ang iniinom mong gamot para sa Diabetes?",
            ["None", "Metformin 500mg tab", "Gliclazide 80mg tab", "Insulin Injection", "Other"]
        )

        has_htn = st.selectbox("May ada ka ba High blood / Hypertension?*", ["Wala", "Meron", "Diri ak maaram"])
        htn_meds = st.selectbox(
            "Ano ang iniinom mong gamot para sa Hypertension?",
            ["None", "Amlodipine 5mg/10mg tab", "Losartan 50mg tab", "Telmisartan 40mg tab", "Captopril 25mg tab", "Other"]
        )

        cholesterol = st.selectbox("Hitaas ba an iyo cholesterol?*", ["Hindi", "Oo", "Diri ak maaram"])

        st.write("Na-diagnose na po ba kamo hinin mga sakit? (High Risk Referral):")
        cvd_stroke = st.checkbox("History of CVD (Stroke)")
        heart_attack = st.checkbox("History of Heart attack (Naatake sa puso)")
        kidney_prob = st.checkbox("Chronic Kidney Problem (Dialysis patient)")

        fam_history = st.selectbox("Family History: May ada ba inatake ha puso o na-stroke?", ["Wala", "Meron"])

        st.write("**4. Blood Pressure Screening**")
        bp1 = st.text_input("Unang Blood Pressure (e.g., 120/80)*")

        systolic = 120
        if bp1 and "/" in bp1:
            try:
                systolic = int(bp1.split("/")[0])
            except ValueError:
                pass

        bp2, bp3, bp_avg = "", "", bp1
        if systolic >= 140:
            st.warning("BP is ≥ 140/90. Rest for 15 minutes and retake twice.")
            bp2 = st.text_input("Pangalawang Blood Pressure (optional)")
            bp3 = st.text_input("Pangatlong Blood Pressure (optional)")

        st.write("**5. Lifestyle & Risk Stratification**")
        smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo"])
        drinker = st.radio("Ikaw ba ay binge drinker?*", ["Hindi", "Oo"])
        exercise = st.radio("Nakakapag-ehersisyo ka ba 150 mins/week?*", ["Oo", "Hindi"])
        healthy_diet = st.radio("Nakakakain ng 5 platitong gulay/prutas araw-araw?*", ["Oo", "Hindi"])

        risk_level, risk_pct = calculate_cvd_risk(age, sex, smoker, systolic, bmi, has_diabetes)
        st.markdown(f"#### **WHO/ISH Risk Level:** {risk_level} Risk ({risk_pct})")

        action = st.selectbox(
            "Ano ang ginawa? / Action Taken*",
            [
                "Advise sa diet at lifestyle",
                "Ni-refer kay midwife para sa kumpletong assessment",
                "Ni-refer sa RHU",
                "Nirefer sa ospital",
                "Nirefer sa RHU/Ospital pero tumanggi",
            ],
        )

        bhw_name = st.text_input("Pangalan ng BHW na nag-assess*")

        submit_assessment = st.form_submit_button("Save Assessment Record")

        if submit_assessment:
            conn = sqlite3.connect("philpen_palo.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO assessments (
                    assessment_date, last_name, first_name, middle_name, zone, barangay,
                    birthday, age, sex, weight_kg, height_cm, bmi, bmi_class, waist_cm,
                    waist_risk, has_diabetes, diabetes_meds, has_hypertension, hypertension_meds,
                    high_cholesterol, history_cvd_stroke, history_heart_attack, history_kidney,
                    family_history, bp_1, bp_2, bp_3, bp_avg, is_smoker, is_binge_drinker,
                    is_exercising, eats_healthy, risk_level, action_taken, bhw_name
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    str(assessment_date), last_name, first_name, middle_name, zone,
                    st.session_state["user_brgy"], str(dob), age, sex, weight, height,
                    bmi, bmi_cat, waist, waist_risk, has_diabetes, diabetes_meds,
                    has_htn, htn_meds, cholesterol, int(cvd_stroke), int(heart_attack),
                    int(kidney_prob), fam_history, bp1, bp2, bp3, bp_avg, smoker,
                    drinker, exercise, healthy_diet, risk_level, action, bhw_name
                ),
            )
            conn.commit()
            conn.close()
            st.success("Assessment record successfully saved!")

# ---------------------------------------------------------
# MODULE 3: PHILPEN DATA ANALYTICS & REPORTS
# ---------------------------------------------------------
elif menu == "📈 PhilPEN Data Analytics":
    st.subheader(f"PhilPEN Analytics & Health Indicators — Brgy. {st.session_state['user_brgy']}")

    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query("SELECT * FROM assessments WHERE barangay = ?", conn, params=(st.session_state["user_brgy"],))
    conn.close()

    if df.empty:
        st.warning("No PhilPEN assessment records found for this barangay yet.")
    else:
        # Filtered Datasets
        adults_df = df[(df["age"] >= 20) & (df["age"] <= 64)]
        seniors_df = df[df["age"] >= 65]
        rhu_referred_df = df[df["action_taken"].str.contains("RHU", case=False, na=False)]
        diabetic_df = df[df["has_diabetes"] == "Meron"]
        hypertensive_df = df[df["has_hypertension"] == "Meron"]

        # Metric Overview Cards
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        col_a.metric("Assessed Adults (20-64)", len(adults_df))
        col_b.metric("Assessed Seniors (65+)", len(seniors_df))
        col_c.metric("RHU Referrals", len(rhu_referred_df))
        col_d.metric("Diabetic Patients", len(diabetic_df))
        col_e.metric("Hypertensive Patients", len(hypertensive_df))

        st.markdown("---")

        # Tabs for Requested Specific Lists
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Masterlist (All Assessed)",
            "🏥 RHU Referrals",
            "🩸 Diabetic Patients",
            "🫀 Hypertensive Patients"
        ])

        with tab1:
            st.write(f"**Complete List of Assessed Individuals ({len(df)} total)**")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.write(f"**List of Patients Referred to RHU ({len(rhu_referred_df)} total)**")
            if not rhu_referred_df.empty:
                display_cols = ["id", "last_name", "first_name", "age", "sex", "zone", "bp_1", "has_diabetes", "has_hypertension", "action_taken", "bhw_name"]
                st.dataframe(rhu_referred_df[display_cols], use_container_width=True)
            else:
                st.info("No patients currently referred to RHU.")

        with tab3:
            st.write(f"**List of Diabetic Patients ({len(diabetic_df)} total)**")
            if not diabetic_df.empty:
                display_cols = ["id", "last_name", "first_name", "age", "sex", "zone", "diabetes_meds", "risk_level", "bhw_name"]
                st.dataframe(diabetic_df[display_cols], use_container_width=True)
            else:
                st.info("No diabetic patients registered.")

        with tab4:
            st.write(f"**List of Hypertensive Patients ({len(hypertensive_df)} total)**")
            if not hypertensive_df.empty:
                display_cols = ["id", "last_name", "first_name", "age", "sex", "zone", "bp_1", "hypertension_meds", "risk_level", "bhw_name"]
                st.dataframe(hypertensive_df[display_cols], use_container_width=True)
            else:
                st.info("No hypertensive patients registered.")

        # CSV Download Section
        st.markdown("---")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Download Full Analytics Export (CSV)",
            data=csv_data,
            file_name=f"PhilPEN_Analytics_Brgy_{st.session_state['user_brgy']}.csv",
            mime="text/csv",
        )

# ---------------------------------------------------------
# FUTURE MODULE PLACEHOLDERS
# ---------------------------------------------------------
else:
    st.subheader(menu)
    st.info("💡 This program module is scheduled for future deployment. Assessment and recording interfaces will be activated soon.")
