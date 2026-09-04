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
            action_taken TEXT
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
# COMPUTATION HELPER FUNCTIONS
# ---------------------------------------------------------
def calculate_age(born):
    today = datetime.date.today()
    return (
        today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    )


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
            return "High", "20% to <30%", "Red"
        return "Medium", "10% to <20%", "Orange"
    elif smoker == "Oo" or sbp >= 140:
        return "Mild", "5% to <10%", "Yellow"
    return "Low", "<5%", "Green"


# ---------------------------------------------------------
# STREAMLIT CONFIG & HIGH-CONTRAST STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="e-FHSIS: Palo, Leyte", layout="wide"
)

# Custom High-Contrast CSS: Light Green Inputs, White Background, Black Text
st.markdown(
    """
    <style>
    /* Main application background to pure white */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* All body text, labels, headers, and form titles forced to sharp black */
    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown, div[role="radiogroup"] label {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* Light Green Entry Boxes (Text inputs, Selectboxes, Number inputs, Date pickers) */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    input, textarea, select {
        background-color: #e8f5e9 !important; /* Soft light green tint */
        color: #000000 !important;
        border: 1px solid #81c784 !important;
        border-radius: 6px !important;
    }

    /* Dropdown text & option legibility */
    div[data-baseweb="select"] *, div[role="listbox"] * {
        color: #000000 !important;
    }

    /* Manila / Light Green Header Banner */
    .header-container {
        background-color: #d4edda;
        border: 2px solid #b1dfbb;
        border-left: 8px solid #28a745;
        padding: 20px;
        border-radius: 6px;
        text-align: center;
        margin-bottom: 25px;
    }
    .header-container h1 {
        color: #155724 !important;
        margin: 0;
        font-weight: 800;
        font-size: 2.1rem;
    }
    .header-container p {
        color: #1e4620 !important;
        margin: 6px 0 0 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #dee2e6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Title Banner
st.markdown(
    """
    <div class="header-container">
        <h1>e-FHSIS: Electronic Field Health Services Information System</h1>
        <p>Palo, Leyte — Rural Health Unit Data Management Portal</p>
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
    st.subheader("Barangay Health Portal Login")

    with st.form("login_form"):
        username = st.selectbox("Select Barangay (Username)", list(BARANGAY_CREDENTIALS.keys()))
        password = st.text_input("Barangay Access Password", type="password")
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
# SIDEBAR NAVIGATION (PROGRAMS MODULE LIST)
# ---------------------------------------------------------
st.sidebar.markdown(f"### 📍 **Barangay {st.session_state['user_brgy']}**")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Health Programs Navigation**")

nav_program = st.sidebar.radio(
    "Select Program Module:",
    [
        "PhilPEN risk assessment",
        "Nutritional Status of 0-59 months old",
        "Expanded Program on Immunization",
        "Maternal Care",
        "Schistosomiasis",
        "NTP",
        "Barangay Database (PhilPEN Records)",
    ],
)

# ---------------------------------------------------------
# PROGRAM MODULE ROUTING
# ---------------------------------------------------------
if nav_program == "PhilPEN risk assessment":
    st.subheader(f"PhilPEN Risk Assessment Form — Barangay {st.session_state['user_brgy']}")

    with st.form("assessment_form"):
        st.markdown("**1. General Information**")
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

        st.markdown("**2. Body Measurements & Auto-Calculations**")
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

        st.markdown("**3. Medical History**")
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"])
        diabetes_meds = st.text_input("Ano ang iniinom mong gamot para sa Diabetes?")

        has_htn = st.selectbox("May ada ka ba High blood / Hypertension?*", ["Wala", "Meron", "Diri ak maaram"])
        htn_meds = st.text_input("Ano ang iniinom mong gamot para sa Hypertension?")

        cholesterol = st.selectbox("Hitaas ba an iyo cholesterol?*", ["Hindi", "Oo", "Diri ak maaram"])

        st.write("Na-diagnose na po ba kamo hinin mga sakit?")
        cvd_stroke = st.checkbox("History of CVD (Stroke)")
        heart_attack = st.checkbox("History of Heart attack (Naatake sa puso)")
        kidney_prob = st.checkbox("Chronic Kidney Problem (Dialysis patient)")

        fam_history = st.selectbox("Family History: May ada ba inatake ha puso o na-stroke?", ["Wala", "Meron"])

        st.markdown("**4. Blood Pressure Screening**")
        bp1 = st.text_input("Unang Blood Pressure (e.g., 120/80)*")

        systolic = 120
        if bp1 and "/" in bp1:
            try:
                systolic = int(bp1.split("/")[0])
            except ValueError:
                pass

        bp2, bp3, bp_avg = "", "", bp1
        if systolic >= 140:
            st.warning("BP is ≥ 140/90. Please rest for 15 minutes and retake.")
            bp2 = st.text_input("Pangalawang Blood Pressure (optional)")
            bp3 = st.text_input("Pangatlong Blood Pressure (optional)")
            if bp2 and bp3 and "/" in bp2 and "/" in bp3:
                try:
                    s2, _ = map(int, bp2.split("/"))
                    s3, _ = map(int, bp3.split("/"))
                    bp_avg = f"{(s2+s3)//2}"
                except ValueError:
                    pass

        st.markdown("**5. Lifestyle & Risk Stratification**")
        smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo"])
        drinker = st.radio("Ikaw ba ay binge drinker?*", ["Hindi", "Oo"])
        exercise = st.radio("Nakakapag-ehersisyo ka ba 150 mins/week?*", ["Oo", "Hindi"])
        healthy_diet = st.radio("Nakakakain ng 5 platitong gulay/prutas araw-araw?*", ["Oo", "Hindi"])

        risk_level, risk_pct, risk_color = calculate_cvd_risk(age, sex, smoker, systolic, bmi, has_diabetes)
        st.markdown(f"#### **WHO/ISH Risk Assessment: {risk_level} Risk ({risk_pct})**")

        action = st.selectbox(
            "Ano ang ginawa? / Action Taken*",
            [
                "Advise sa diet at lifestyle (Counselling)",
                "Ni-refer kay midwife para sa kumpletong assessment",
                "Ni-refer sa RHU Physician",
                "Urgent referral sa Ospital / Physician",
                "Nirefer sa RHU/Ospital pero tumanggi",
            ],
        )

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
                    is_exercising, eats_healthy, risk_level, action_taken
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    str(assessment_date),
                    last_name,
                    first_name,
                    middle_name,
                    zone,
                    st.session_state["user_brgy"],
                    str(dob),
                    age,
                    sex,
                    weight,
                    height,
                    bmi,
                    bmi_cat,
                    waist,
                    waist_risk,
                    has_diabetes,
                    diabetes_meds,
                    has_htn,
                    htn_meds,
                    cholesterol,
                    int(cvd_stroke),
                    int(heart_attack),
                    int(kidney_prob),
                    fam_history,
                    bp1,
                    bp2,
                    bp3,
                    bp_avg,
                    smoker,
                    drinker,
                    exercise,
                    healthy_diet,
                    risk_level,
                    action,
                ),
            )
            conn.commit()
            conn.close()
            st.success("Record successfully saved to the barangay database!")

elif nav_program == "Barangay Database (PhilPEN Records)":
    st.subheader(f"PhilPEN Database — Barangay {st.session_state['user_brgy']}")

    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query(
        "SELECT * FROM assessments WHERE barangay = ?",
        conn,
        params=(st.session_state["user_brgy"],),
    )
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Export CSV ({st.session_state['user_brgy']})",
            data=csv,
            file_name=f"PhilPEN_Records_{st.session_state['user_brgy']}.csv",
            mime="text/csv",
        )
    else:
        st.info(f"No records found for Barangay {st.session_state['user_brgy']}.")

else:
    st.subheader(f"{nav_program} Module")
    st.info(
        f"The **{nav_program}** program module is scheduled for data integration. "
        "PhilPEN risk assessment is currently the active module for data entry."
    )
