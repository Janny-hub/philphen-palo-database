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
            assessment_year INTEGER,
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
            history_other TEXT,
            family_history TEXT,
            bp_1 TEXT,
            bp_2 TEXT,
            bp_3 TEXT,
            bp_avg TEXT,
            is_hypertensive_flag INTEGER,
            is_smoker TEXT,
            is_binge_drinker TEXT,
            is_exercising TEXT,
            eats_healthy TEXT,
            risk_level TEXT,
            risk_percent TEXT,
            action_taken TEXT,
            bhw_name TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()

# ---------------------------------------------------------
# BARANGAY CREDENTIALS (Username: Password)
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
# COMPUTATION & VALIDATION HELPER FUNCTIONS
# ---------------------------------------------------------
def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def calculate_bmi(weight, height):
    if height > 0:
        return round((weight / height / height) * 10000, 2)
    return 0.0


def classify_bmi_asia_pacific(bmi):
    """PhilPEN WHO Asia-Pacific BMI Classification"""
    if bmi < 18.5:
        return "< 18.5 (UNDERWEIGHT)"
    elif 18.5 <= bmi <= 22.9:
        return "18.5 - 22.9 (NORMAL)"
    elif 23.0 <= bmi <= 24.9:
        return "23.0 - 24.9 (OVERWEIGHT OR AT RISK)"
    elif 25.0 <= bmi <= 29.9:
        return "25.0 - 29.9 (OBESE I)"
    else:
        return "≥ 30.0 (OBESE II)"


def classify_waist(sex, waist):
    if sex == "Male":
        return "AT RISK (≥ 90 cm)" if waist >= 90 else "NOT AT RISK (< 90 cm)"
    elif sex == "Female":
        return "AT RISK (≥ 80 cm)" if waist >= 80 else "NOT AT RISK (< 80 cm)"
    return "N/A"


def parse_bp(bp_str):
    """Extract Systolic and Diastolic pressure values safely."""
    try:
        if "/" in bp_str:
            parts = bp_str.strip().split("/")
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return 0, 0


def calculate_who_cvd_risk_2019(age, sex, smoker, sbp, bmi, diabetes, cvd_history):
    """2019 WHO CVD Risk Non-laboratory-based Stratification for Southeast Asia"""
    if cvd_history or sbp >= 180:
        return "Very High", "> 30%", "#7209b7", "Urgent referral sa Physician o Ospital"
    elif diabetes == "Meron" or (sbp >= 160 and age >= 60):
        return "High", "20% - 30%", "#d90429", "Urgent referral sa RHU / Physician"
    elif sbp >= 160 or (sbp >= 140 and bmi >= 25.0) or (smoker == "Oo" and age >= 50):
        return "Medium", "10% - 20%", "#f77f00", "Ni-refer sa RHU Physician"
    elif sbp >= 140 or smoker == "Oo" or bmi >= 23.0:
        return "Mild", "5% - 10%", "#eaaa00", "Ni-refer kay midwife para sa kumpletong assessment"
    else:
        return "Low", "< 5%", "#2a9d8f", "Advise sa diet at lifestyle (Counselling only)"


def check_duplicate_entry(first_name, last_name, middle_name, barangay, year):
    """Check if patient has already been assessed in the current calendar year."""
    conn = sqlite3.connect("philpen_palo.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, assessment_date FROM assessments 
        WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(?))
          AND LOWER(TRIM(last_name)) = LOWER(TRIM(?))
          AND LOWER(TRIM(middle_name)) = LOWER(TRIM(?))
          AND barangay = ?
          AND assessment_year = ?
    """,
        (first_name, last_name, middle_name, barangay, year),
    )
    result = c.fetchone()
    conn.close()
    return result


# ---------------------------------------------------------
# STREAMLIT CONFIG & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="Palo PhilPEN System", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #f4f6f8; }
    
    .header-container {
        background: linear-gradient(90deg, #d90429 0%, #ffb703 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .header-container h1 { color: #ffffff !important; margin: 0; font-weight: 700; }
    .header-container p { color: #fff3bf; margin: 5px 0 0 0; font-size: 1.1rem; }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header-container">
        <h1>PhilPEN Risk Assessment & Analytics System</h1>
        <p>Municipality of Palo, Leyte — Rural Health Unit</p>
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
        username = st.selectbox("Barangay Name (Username)", list(BARANGAY_CREDENTIALS.keys()))
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
    "Navigation Menu",
    [
        "📊 Dashboard Overview",
        "📋 PhilPEN Risk Assessment",
        "📈 PhilPEN Data Analytics",
        "👶 Nutritional Status (0-59 mos)",
        "💉 Expanded Program on Immunization",
        "🤰 Maternal Care",
        "🐌 Schistosomiasis",
        "🫁 NTP (National TB Program)",
    ],
)

# ---------------------------------------------------------
# MODULE 1: DASHBOARD OVERVIEW
# ---------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.subheader(f"Welcome, Health Personnel of Brgy. {st.session_state['user_brgy']}!")

    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query("SELECT * FROM assessments WHERE barangay = ?", conn, params=(st.session_state["user_brgy"],))
    conn.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Screened", len(df))
    m2.metric("Adults (20-64 yrs)", len(df[(df["age"] >= 20) & (df["age"] <= 64)]))
    m3.metric("Seniors (65+ yrs)", len(df[df["age"] >= 65]))
    m4.metric("RHU Referrals", len(df[df["action_taken"].str.contains("RHU|Physician|Ospital", case=False, na=False)]))

# ---------------------------------------------------------
# MODULE 2: PHILPEN RISK ASSESSMENT FORM
# ---------------------------------------------------------
elif menu == "📋 PhilPEN Risk Assessment":
    st.subheader(f"PhilPEN Risk Assessment Form — Brgy. {st.session_state['user_brgy']}")

    with st.form("assessment_form"):
        st.write("**1. General Patient Information**")
        
        # Name fields placed side-by-side
        col_last, col_first, col_mid = st.columns(3)
        with col_last:
            last_name = st.text_input("Apilido (Last Name)*")
        with col_first:
            first_name = st.text_input("Pangalan (Given Name)*")
        with col_mid:
            middle_name = st.text_input("Gitnang Pangalan (Middle Name)")

        col_date, col_zone, col_brgy = st.columns(3)
        with col_date:
            assessment_date = st.date_input("Date of Assessment*", datetime.date.today())
        with col_zone:
            zone = st.text_input("Zone / Purok*")
        with col_brgy:
            barangay = st.text_input("Barangay", value=st.session_state["user_brgy"], disabled=True)

        col_dob, col_sex = st.columns(2)
        with col_dob:
            dob = st.date_input("Birthday*", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            age = calculate_age(dob)
            st.info(f"**Calculated Age:** {age} years old")
        with col_sex:
            sex = st.radio("Sex*", ["Male", "Female", "Other"])

        st.markdown("---")
        st.write("**2. Body Measurements & Auto-Calculations**")
        col_w, col_h = st.columns(2)
        with col_w:
            weight = st.number_input("Timbang / Weight (kg)*", min_value=1.0, max_value=300.0, step=0.5)
        with col_h:
            height = st.number_input("Taas / Height (cm)*", min_value=30.0, max_value=250.0, step=0.5)

        bmi = calculate_bmi(weight, height)
        bmi_cat = classify_bmi_asia_pacific(bmi)
        st.success(f"**Calculated BMI:** {bmi} | **Asia-Pacific Classification:** {bmi_cat}")

        waist = st.number_input("Waist Circumference (cm)*", min_value=20.0, max_value=200.0, step=0.5)
        waist_risk = classify_waist(sex, waist)
        st.info(f"**Waist Risk Status:** {waist_risk}")

        st.markdown("---")
        st.write("**3. Medical History**")
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"])
        diabetes_meds = st.selectbox(
            "Ano ang iniinom mong gamot para sa Diabetes?",
            ["Wala", "Metformin 500mg tab", "Gliclazide 80mg tab", "Insulin Injection", "Other"]
        )

        has_htn = st.selectbox("May ada ka ba High blood / Hypertension?*", ["Wala", "Meron", "Diri ak maaram"])
        htn_meds = st.selectbox(
            "Ano ang iniinom mong gamot para sa Hypertension?",
            ["Wala", "Amlodipine 5mg/10mg tab", "Losartan 50mg tab", "Telmisartan 40mg tab", "Captopril 25mg tab", "Other"]
        )

        cholesterol = st.selectbox("Hitaas ba an iyo cholesterol?*", ["Hindi", "Oo", "Diri ak maaram", "Other"])

        st.write("Na diagnose na po ba kamo hinin mga sakit: *(Kung oo, i-refer sa RHU)*")
        cvd_stroke = st.checkbox("History of CVD (Stroke)")
        heart_attack = st.checkbox("History of Heart attack (Naatake sa puso)")
        kidney_prob = st.checkbox("Chronic Kidney Problem (Dialysis patient)")
        other_diag = st.text_input("Other Diagnosis / Medical History (Optional):")

        fam_history = st.selectbox(
            "Ha iyo mga bugto, nanay, o tatay, may ada ba inatake ha puso o na stroke?*",
            ["Wala", "Meron", "Other"]
        )

        st.markdown("---")
        st.write("**4. Blood Pressure Screening**")
        bp1 = st.text_input("Unang Blood Pressure (e.g., 140/90)*")

        sbp1, dbp1 = parse_bp(bp1)
        
        # Auto-flag Hypertensive status
        is_htn_flag = 1 if (sbp1 >= 140 or dbp1 >= 90 or has_htn == "Meron") else 0
        if is_htn_flag:
            st.error("⚠️ **FLAGGED:** Patient meets criteria for Hypertension (BP ≥ 140/90 or existing diagnosis).")

        bp2, bp3, bp_avg = "", "", bp1
        if sbp1 >= 140 or dbp1 >= 90:
            st.warning("BP is ≥ 140/90. Rest for 15 minutes before repeating measurement.")
            bp2 = st.text_input("Pangalawang Blood Pressure (optional)")
            bp3 = st.text_input("Pangatlong Blood Pressure (optional)")

        st.markdown("---")
        st.write("**5. Lifestyle Inputs**")
        smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo", "Other"])
        drinker = st.radio("Ikaw ba binge drinker o nakakalimang baso ka ba ng alak sa isang okasyon?*", ["Hindi", "Oo"])
        exercise = st.radio("Nakakapag ehersisyo ka ba ng 150 minutes sa loob ng isang linggo?*", ["Oo", "Hindi"])
        healthy_diet = st.radio("Nakakakain ka ba ng 5 platitong gulay o kaya limang prutas sa loob ng sang araw?*", ["Oo", "Hindi"])

        # Risk Stratification Calculation
        cvd_history = cvd_stroke or heart_attack or kidney_prob
        risk_lvl, risk_pct, risk_hex, rec_action = calculate_who_cvd_risk_2019(
            age, sex, smoker, sbp1, bmi, has_diabetes, cvd_history
        )

        st.markdown("---")
        st.write("**6. 2019 WHO CVD Risk Stratification**")
        st.markdown(
            f"""
            <div style="background-color:{risk_hex}; padding:15px; border-radius:8px; color:white;">
                <h3 style="margin:0; color:white;">Calculated Risk: {risk_lvl} ({risk_pct})</h3>
                <p style="margin:5px 0 0 0; font-size:1.1rem;">Recommended Action: <b>{rec_action}</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action = st.selectbox(
            "Ano ang ginawa?*",
            [
                "Advise sa diet at lifestyle",
                "Ni-refer kay midwife para sa kumpletong assessment",
                "Ni-refer sa RHU",
                "Nirefer sa ospital",
                "Nirefer sa RHU/ Ospital pero tumanggi",
                "Other",
            ],
            index=0
        )

        bhw_name = st.text_input("Pangalan ng BHW na nag-assess:*")

        submit_assessment = st.form_submit_button("Save Assessment Record")

        if submit_assessment:
            current_year = assessment_date.year
            duplicate = check_duplicate_entry(
                first_name, last_name, middle_name, st.session_state["user_brgy"], current_year
            )

            if duplicate:
                st.error(
                    f"⚠️ **DUPLICATE ENTRY PROMPT:** Patient **{first_name} {middle_name} {last_name}** "
                    f"already has an assessment record (ID #{duplicate[0]} on {duplicate[1]}) for year {current_year}. "
                    f"PhilPEN assessment is conducted ONLY ONCE A YEAR per individual."
                )
            elif not first_name or not last_name or not bhw_name:
                st.warning("Please fill out all required fields marked with * before saving.")
            else:
                conn = sqlite3.connect("philpen_palo.db")
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO assessments (
                        assessment_date, assessment_year, last_name, first_name, middle_name, zone, barangay,
                        birthday, age, sex, weight_kg, height_cm, bmi, bmi_class, waist_cm,
                        waist_risk, has_diabetes, diabetes_meds, has_hypertension, hypertension_meds,
                        high_cholesterol, history_cvd_stroke, history_heart_attack, history_kidney, history_other,
                        family_history, bp_1, bp_2, bp_3, bp_avg, is_hypertensive_flag, is_smoker, is_binge_drinker,
                        is_exercising, eats_healthy, risk_level, risk_percent, action_taken, bhw_name
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                    (
                        str(assessment_date), current_year, last_name, first_name, middle_name, zone,
                        st.session_state["user_brgy"], str(dob), age, sex, weight, height,
                        bmi, bmi_cat, waist, waist_risk, has_diabetes, diabetes_meds,
                        has_htn, htn_meds, cholesterol, int(cvd_stroke), int(heart_attack),
                        int(kidney_prob), other_diag, fam_history, bp1, bp2, bp3, bp_avg,
                        is_htn_flag, smoker, drinker, exercise, healthy_diet, risk_lvl,
                        risk_pct, action, bhw_name
                    ),
                )
                conn.commit()
                conn.close()
                st.success("Assessment record successfully saved!")

# ---------------------------------------------------------
# MODULE 3: PHILPEN DATA ANALYTICS & REPORTS
# ---------------------------------------------------------
elif menu == "📈 PhilPEN Data Analytics":
    st.subheader(f"PhilPEN Analytics & Indicator Reports — Brgy. {st.session_state['user_brgy']}")

    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query("SELECT * FROM assessments WHERE barangay = ?", conn, params=(st.session_state["user_brgy"],))
    conn.close()

    if df.empty:
        st.warning("No PhilPEN assessment records found for this barangay.")
    else:
        # Analytics calculations
        adults_df = df[(df["age"] >= 20) & (df["age"] <= 64)]
        seniors_df = df[df["age"] >= 65]
        rhu_referred_df = df[df["action_taken"].str.contains("RHU", case=False, na=False)]
        diabetic_df = df[df["has_diabetes"] == "Meron"]
        hypertensive_df = df[(df["has_hypertension"] == "Meron") | (df["is_hypertensive_flag"] == 1)]

        # Key Indicator Cards
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Assessed Adults (20-64)", len(adults_df))
        c2.metric("Assessed Seniors (65+)", len(seniors_df))
        c3.metric("RHU Referrals", len(rhu_referred_df))
        c4.metric("Diabetic Patients", len(diabetic_df))
        c5.metric("Hypertensive Patients", len(hypertensive_df))

        st.markdown("---")

        # Tabs for Requested Views
        t1, t2, t3, t4 = st.tabs([
            "📋 Masterlist (All Assessed)",
            "🏥 RHU Referrals",
            "🩸 Diabetic Patients",
            "🫀 Hypertensive Patients"
        ])

        name_cols = ["id", "last_name", "first_name", "middle_name", "age", "sex", "zone", "assessment_date", "bhw_name"]

        with t1:
            st.write(f"**List ng lahat ng na-aassess ({len(df)} patients)**")
            st.dataframe(df, use_container_width=True)

        with t2:
            st.write(f"**Number of Patients Referred to RHU: {len(rhu_referred_df)}**")
            if not rhu_referred_df.empty:
                st.dataframe(rhu_referred_df[name_cols + ["risk_level", "action_taken"]], use_container_width=True)

        with t3:
            st.write(f"**List of Diabetic Patients ({len(diabetic_df)} total)**")
            if not diabetic_df.empty:
                st.dataframe(diabetic_df[name_cols + ["diabetes_meds", "risk_level"]], use_container_width=True)

        with t4:
            st.write(f"**List of Hypertensive Patients ({len(hypertensive_df)} total)**")
            if not hypertensive_df.empty:
                st.dataframe(hypertensive_df[name_cols + ["bp_1", "hypertension_meds", "risk_level"]], use_container_width=True)

        st.markdown("---")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export Barangay Assessment Database (CSV)",
            data=csv_data,
            file_name=f"PhilPEN_Analytics_Brgy_{st.session_state['user_brgy']}.csv",
            mime="text/csv",
        )

# ---------------------------------------------------------
# FUTURE MODULE PLACEHOLDERS
# ---------------------------------------------------------
else:
    st.subheader(menu)
    st.info("This program module is active and reserved for future data entry expansion.")
