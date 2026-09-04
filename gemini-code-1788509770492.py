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
# COMMON PHILIPPINE MEDICATIONS LIST
# ---------------------------------------------------------
DIABETES_MEDICATIONS = [
    "Wala / None",
    "Metformin (500mg/850mg)",
    "Gliclazide (30mg/80mg)",
    "Glimepiride (2mg/4mg)",
    "Insulin Human NPH / Regular",
    "Sitagliptin",
    "Empagliflozin",
    "Iba pa (Others)",
]

HYPERTENSION_MEDICATIONS = [
    "Wala / None",
    "Amlodipine (5mg/10mg)",
    "Losartan (50mg/100mg)",
    "Metoprolol (50mg/100mg)",
    "Captopril (25mg)",
    "Enalapril (5mg/20mg)",
    "Hydrochlorothiazide / HCTZ (12.5mg/25mg)",
    "Telmisartan (40mg/80mg)",
    "Carvedilol (6.25mg/12.5mg)",
    "Iba pa (Others)",
]

# ---------------------------------------------------------
# HELPER CALCULATIONS & DUPLICATE CHECK
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
            return "High", "20% to <30%", "Red"
        return "Medium", "10% to <20%", "Orange"
    elif smoker == "Oo" or sbp >= 140:
        return "Mild", "5% to <10%", "Yellow"
    return "Low", "<5%", "Green"


def check_annual_duplicate(first_name, last_name, dob, year, exclude_id=None):
    if not first_name.strip() or not last_name.strip():
        return False, None

    conn = sqlite3.connect("philpen_palo.db")
    c = conn.cursor()

    query = """
        SELECT id, assessment_date FROM assessments 
        WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(?))
          AND LOWER(TRIM(last_name)) = LOWER(TRIM(?))
          AND birthday = ?
          AND strftime('%Y', assessment_date) = ?
    """
    params = [first_name, last_name, str(dob), str(year)]

    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)

    c.execute(query, params)
    result = c.fetchone()
    conn.close()

    if result:
        return True, result[1]
    return False, None


# ---------------------------------------------------------
# STREAMLIT CONFIG & HIGH-CONTRAST MODERN STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="e-FHSIS | Palo, Leyte Portal", layout="wide", page_icon="🏥")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Force Light Theme Canvas & High-Contrast Dark Text globally */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* ALL Labels, Paragraphs, Headings forced to High-Contrast Slate Dark */
    p, span, label, h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stMarkdown *,
    div[role="radiogroup"] label,
    div[role="group"] label,
    [data-testid="stWidgetLabel"] * {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* Crisp Input Boxes (White Background + Dark Slate Text + Dark Border) */
    input, textarea, select,
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #64748b !important;
        border-radius: 8px !important;
    }

    /* Direct text inside HTML input tags */
    input, textarea {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* Fix Date Picker Input Text Visibility */
    .stDateInput input,
    div[data-baseweb="datepicker"] input,
    div[data-baseweb="datepicker"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Popover, Calendar, Dropdown Menus */
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[role="listbox"] *,
    div[role="dialog"] * {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    /* Multiselect Badge Tags */
    span[data-baseweb="tag"] {
        background-color: #0f766e !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] * {
        color: #ffffff !important;
    }

    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #0284c7 0%, #0f766e 100%);
        padding: 24px 30px;
        border-radius: 14px;
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(15, 118, 110, 0.2);
        margin-bottom: 25px;
    }
    .header-banner h1 {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .header-banner p {
        color: #e0f2fe !important;
        font-size: 1rem !important;
        margin-top: 6px !important;
        font-weight: 500 !important;
    }

    /* Modern KPI Cards with High Contrast */
    .kpi-card {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    .kpi-label {
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .kpi-value {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin-top: 4px !important;
    }
    .kpi-subtext {
        font-size: 0.825rem !important;
        font-weight: 600 !important;
        color: #0f766e !important;
    }

    /* Red Flag Banner for Double Entry */
    .flag-red-card {
        background-color: #fef2f2 !important;
        border: 2px solid #fca5a5 !important;
        border-left: 8px solid #dc2626 !important;
        padding: 16px !important;
        border-radius: 10px !important;
        margin-bottom: 20px !important;
    }
    .flag-red-card h4 {
        color: #991b1b !important;
        margin: 0 0 6px 0 !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
    }
    .flag-red-card p {
        color: #7f1d1d !important;
        margin: 0 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    /* Buttons */
    .stButton > button {
        background: #0f766e !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 10px rgba(15, 118, 110, 0.25) !important;
    }
    .stButton > button:hover {
        background: #115e59 !important;
        color: #ffffff !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1.5px solid #e2e8f0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Title Banner
st.markdown(
    """
    <div class="header-banner">
        <h1>e-FHSIS Healthcare Portal</h1>
        <p>Rural Health Unit Data Management & PhilPEN Analytics — Palo, Leyte</p>
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
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown(f"### 📍 **Barangay {st.session_state['user_brgy']}**")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation Menu**")

nav_program = st.sidebar.radio(
    "Select Portal View:",
    [
        " Executive Dashboard",
        "PhilPEN Risk Assessment Form",
        "Barangay Database & Analytics",
        "Nutritional Status (0-59 mos)",
        "Expanded Program on Immunization",
        "Maternal Care",
        "Schistosomiasis",
        "NTP",
    ],
)

# Fetch Current Barangay Dataset
conn = sqlite3.connect("philpen_palo.db")
df = pd.read_sql_query(
    "SELECT * FROM assessments WHERE barangay = ?",
    conn,
    params=(st.session_state["user_brgy"],),
)
conn.close()

# ---------------------------------------------------------
# MODULE 1: EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if nav_program == " Executive Dashboard":
    st.subheader(f"Barangay Health Executive Dashboard — {st.session_state['user_brgy']}")

    if df.empty:
        st.info("No resident risk assessment records found. Complete assessments to generate real-time metrics.")
    else:
        # KPI Row
        total_assessed = len(df)
        high_risk = len(df[df["risk_level"] == "High"])
        diabetic_ct = len(df[df["has_diabetes"] == "Meron"])
        hypertensive_ct = len(df[df["has_hypertension"] == "Meron"])
        rhu_ref_ct = len(df[df["action_taken"].astype(str).str.contains("RHU", case=False, na=False)])

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Assessed</div>
                    <div class="kpi-value">{total_assessed}</div>
                    <div class="kpi-subtext">Residents Screened</div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">High CVD Risk</div>
                    <div class="kpi-value" style="color: #dc2626;">{high_risk}</div>
                    <div class="kpi-subtext">Needs Urgent Referral</div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Diabetic Cases</div>
                    <div class="kpi-value" style="color: #d97706;">{diabetic_ct}</div>
                    <div class="kpi-subtext">{round((diabetic_ct/total_assessed)*100, 1) if total_assessed else 0}% Rate</div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with k4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Hypertensive</div>
                    <div class="kpi-value" style="color: #0284c7;">{hypertensive_ct}</div>
                    <div class="kpi-subtext">{round((hypertensive_ct/total_assessed)*100, 1) if total_assessed else 0}% Rate</div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with k5:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">RHU Referrals</div>
                    <div class="kpi-value" style="color: #7c3aed;">{rhu_ref_ct}</div>
                    <div class="kpi-subtext">Physician Care</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Visual Analytics Charts
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### **CVD Risk Stratification Breakdown**")
            risk_counts = df["risk_level"].value_counts()
            st.bar_chart(risk_counts, color="#0f766e")

        with chart_col2:
            st.markdown("#### **Demographics: Age Group & Sex Distribution**")
            bins = [0, 19, 30, 45, 64, 120]
            labels = ["<20", "20-29", "30-44", "45-64", "65+"]
            df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
            age_sex_df = pd.crosstab(df["age_group"], df["sex"])
            st.line_chart(age_sex_df)

        st.markdown("---")

        # Actionable Priority Patients Table
        st.markdown("#### **High-Risk Patients Requiring Immediate Medical Intervention**")
        high_risk_df = df[df["risk_level"] == "High"][
            ["id", "last_name", "first_name", "age", "sex", "zone", "bp_1", "has_diabetes", "action_taken"]
        ]
        if not high_risk_df.empty:
            st.dataframe(high_risk_df, use_container_width=True)
        else:
            st.success("No residents currently categorized as High CVD Risk.")

# ---------------------------------------------------------
# MODULE 2: PHILPEN RISK ASSESSMENT FORM
# ---------------------------------------------------------
elif nav_program == "PhilPEN Risk Assessment Form":
    st.subheader(f"PhilPEN Risk Assessment Form — Barangay {st.session_state['user_brgy']}")

    progress_container = st.container()

    st.markdown("**1. General Information**")
    col1, col2, col3 = st.columns(3)
    with col1:
        assessment_date = st.date_input("Date of Assessment*", datetime.date.today(), key="p_date")
        last_name = st.text_input("Apilido (Last Name)*", key="p_lname")
    with col2:
        first_name = st.text_input("Pangalan (Given Name)*", key="p_fname")
        middle_name = st.text_input("Gitnang Pangalan (Middle Name)", key="p_mname")
    with col3:
        zone = st.text_input("Zone / Purok*", key="p_zone")
        barangay = st.text_input("Barangay", value=st.session_state["user_brgy"], disabled=True)

    col_dob, col_sex = st.columns(2)
    with col_dob:
        dob = st.date_input(
            "Birthday*",
            min_value=datetime.date(1920, 1, 1),
            max_value=datetime.date.today(),
            key="p_dob",
        )
        age = calculate_age(dob)
        st.info(f"**Calculated Age:** {age} years old")
    with col_sex:
        sex = st.radio("Sex*", ["Male", "Female", "Other"], key="p_sex")

    # DOUBLE ENTRY CHECK & RED FLAGGING
    assessment_year = assessment_date.year
    is_duplicate, prev_date = check_annual_duplicate(first_name, last_name, dob, assessment_year)

    if is_duplicate:
        st.markdown(
            f"""
            <div class="flag-red-card">
                <h4>🔴 FLAGGED AS DOUBLE ENTRY (ANNUAL LIMIT EXCEEDED)</h4>
                <p>
                    <strong>{first_name.upper()} {last_name.upper()}</strong> (DOB: {dob}) has already been assessed on 
                    <strong>{prev_date}</strong> for calendar year <strong>{assessment_year}</strong>.<br>
                    ⚠️ <em>Policy: Each resident can only undergo PhilPEN Assessment <u>once per calendar year</u>.</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("**2. Body Measurements & Auto-Calculations**")
    col_w, col_h = st.columns(2)
    with col_w:
        weight = st.number_input("Timbang / Weight (kg)*", min_value=0.0, max_value=300.0, step=0.5, key="p_weight")
    with col_h:
        height = st.number_input("Taas / Height (cm)*", min_value=0.0, max_value=250.0, step=0.5, key="p_height")

    bmi = calculate_bmi(weight, height) if weight > 0 and height > 0 else 0.0
    bmi_cat = classify_bmi(bmi) if bmi > 0 else "N/A"
    st.success(f"**Calculated BMI:** {bmi} | **Classification:** {bmi_cat}")

    waist = st.number_input("Waist Circumference (cm)*", min_value=0.0, max_value=200.0, step=0.5, key="p_waist")
    waist_risk = classify_waist(sex, waist) if waist > 0 else "N/A"
    st.info(f"**Waist Risk Status:** {waist_risk}")

    st.markdown("**3. Medical History & Medications (Philippine Primary Care Standards)**")
    col_diab, col_htn = st.columns(2)

    with col_diab:
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"], key="p_diab")
        diabetes_meds_selected = []
        if has_diabetes == "Meron":
            diabetes_meds_selected = st.multiselect(
                "Ano ang iniinom mong gamot para sa Diabetes?",
                options=DIABETES_MEDICATIONS,
                default=["Metformin (500mg/850mg)"],
                key="p_diab_meds_multi",
            )
        diabetes_meds_str = ", ".join(diabetes_meds_selected) if diabetes_meds_selected else "None"

    with col_htn:
        has_htn = st.selectbox("May ada ka ba High blood / Hypertension?*", ["Wala", "Meron", "Diri ak maaram"], key="p_htn")
        htn_meds_selected = []
        if has_htn == "Meron":
            htn_meds_selected = st.multiselect(
                "Ano ang iniinom mong gamot para sa Hypertension?",
                options=HYPERTENSION_MEDICATIONS,
                default=["Amlodipine (5mg/10mg)"],
                key="p_htn_meds_multi",
            )
        htn_meds_str = ", ".join(htn_meds_selected) if htn_meds_selected else "None"

    cholesterol = st.selectbox("Hitaas ba an iyo cholesterol?*", ["Hindi", "Oo", "Diri ak maaram"], key="p_chol")

    st.write("Na-diagnose na po ba kamo hinin mga sakit?")
    cvd_stroke = st.checkbox("History of CVD (Stroke)", key="p_stroke")
    heart_attack = st.checkbox("History of Heart attack (Naatake sa puso)", key="p_heart")
    kidney_prob = st.checkbox("Chronic Kidney Problem (Dialysis patient)", key="p_kidney")

    fam_history = st.selectbox("Family History: May ada ba inatake ha puso o na-stroke?", ["Wala", "Meron"], key="p_fam")

    st.markdown("**4. Blood Pressure Screening**")
    bp1 = st.text_input("Unang Blood Pressure (e.g., 120/80)*", key="p_bp1")

    systolic = 120
    if bp1 and "/" in bp1:
        try:
            systolic = int(bp1.split("/")[0])
        except ValueError:
            pass

    bp2, bp3, bp_avg = "", "", bp1
    if systolic >= 140:
        st.warning("BP is ≥ 140/90. Please rest for 15 minutes and retake.")
        bp2 = st.text_input("Pangalawang Blood Pressure (optional)", key="p_bp2")
        bp3 = st.text_input("Pangatlong Blood Pressure (optional)", key="p_bp3")

    st.markdown("**5. Lifestyle & Risk Stratification**")
    smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo"], key="p_smoke")
    drinker = st.radio("Ikaw ba ay binge drinker?*", ["Hindi", "Oo"], key="p_drink")
    exercise = st.radio("Nakakapag-ehersisyo ka ba 150 mins/week?*", ["Oo", "Hindi"], key="p_exer")
    healthy_diet = st.radio("Nakakakain ng 5 platitong gulay/prutas araw-araw?*", ["Oo", "Hindi"], key="p_diet")

    risk_level, risk_pct, risk_color = calculate_cvd_risk(age, sex, smoker, systolic, bmi, has_diabetes)
    st.markdown(f"#### **WHO/ISH Risk Assessment: {risk_level} Risk ({risk_pct})**")

    action = st.selectbox(
        "Ano ang ginawa? / Action Taken*",
        [
            "-- Pumili ng Aksyon --",
            "Advise sa diet at lifestyle (Counselling)",
            "Ni-refer kay midwife para sa kumpletong assessment",
            "Ni-refer sa RHU Physician",
            "Urgent referral sa Ospital / Physician",
            "Nirefer sa RHU/Ospital pero tumanggi",
        ],
        key="p_action",
    )

    # Progress Bar Calculations
    required_checks = [
        bool(last_name.strip()),
        bool(first_name.strip()),
        bool(zone.strip()),
        weight > 0,
        height > 0,
        waist > 0,
        bool(bp1.strip()),
        action != "-- Pumili ng Aksyon --",
    ]

    completed_fields = sum(required_checks)
    total_required = len(required_checks)
    progress_pct = int((completed_fields / total_required) * 100)

    with progress_container:
        st.markdown(f"### 📋 **Form Filling Progress:** `{completed_fields}/{total_required} Required Fields ({progress_pct}%)`")
        st.progress(progress_pct / 100)
        st.markdown("---")

    if st.button("Save Assessment Record"):
        if is_duplicate:
            st.error(f"⛔ CANNOT SAVE RECORD: {first_name} {last_name} has already been assessed for {assessment_year}!")
        elif completed_fields < total_required:
            st.error("Paki-kumpleto ang lahat ng mandatory fields (*) bago i-save!")
        else:
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
                    diabetes_meds_str,
                    has_htn,
                    htn_meds_str,
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

# ---------------------------------------------------------
# MODULE 3: DATABASE & ANALYTICS
# ---------------------------------------------------------
elif nav_program == "Barangay Database & Analytics":
    st.subheader(f"PhilPEN Database & Statistical Reports — Barangay {st.session_state['user_brgy']}")

    tab_view, tab_analytics, tab_edit = st.tabs(
        ["📋 View Master Records", "📊 Detailed Analytics & Reports", "✏️ Edit Resident Record"]
    )

    with tab_view:
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

    with tab_analytics:
        if df.empty:
            st.info("No assessment records found to analyze.")
        else:
            adults_20_64 = df[(df["age"] >= 20) & (df["age"] <= 64)]
            seniors_65_plus = df[df["age"] >= 65]
            rhu_referred = df[df["action_taken"].astype(str).str.contains("RHU", case=False, na=False)]
            diabetic_patients = df[df["has_diabetes"] == "Meron"]
            hypertensive_patients = df[df["has_hypertension"] == "Meron"]

            st.markdown("#### **1. Age & Sex Breakdown Table**")
            bins = [0, 19, 30, 45, 64, 120]
            labels = ["< 20 yrs", "20-29 yrs", "30-44 yrs", "45-64 yrs", "65+ yrs"]
            df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
            age_sex_dist = pd.crosstab(df["age_group"], df["sex"], margins=True, margins_name="Total")
            st.dataframe(age_sex_dist, use_container_width=True)

            st.markdown("---")
            st.markdown(f"#### **2 & 3. Key Demographic Cohorts**")
            col_ad, col_sr = st.columns(2)
            with col_ad:
                st.markdown(f"**Adults Assessed (20 - 64 years old):** `{len(adults_20_64)}`")
                if not adults_20_64.empty:
                    st.dataframe(adults_20_64[["id", "last_name", "first_name", "age", "sex", "risk_level"]], use_container_width=True)
            with col_sr:
                st.markdown(f"**Older Adults Assessed (65+ years old):** `{len(seniors_65_plus)}`")
                if not seniors_65_plus.empty:
                    st.dataframe(seniors_65_plus[["id", "last_name", "first_name", "age", "sex", "risk_level"]], use_container_width=True)

            st.markdown("---")
            st.markdown(f"#### **4. Diabetic Patients Master List (`{len(diabetic_patients)}`)**")
            if not diabetic_patients.empty:
                st.dataframe(diabetic_patients[["id", "last_name", "first_name", "age", "diabetes_meds", "risk_level"]], use_container_width=True)

            st.markdown(f"#### **5. Hypertensive Patients Master List (`{len(hypertensive_patients)}`)**")
            if not hypertensive_patients.empty:
                st.dataframe(hypertensive_patients[["id", "last_name", "first_name", "age", "bp_1", "hypertension_meds", "risk_level"]], use_container_width=True)

    with tab_edit:
        if df.empty:
            st.info("No records available to edit.")
        else:
            resident_options = {
                f"ID {row['id']}: {row['last_name']}, {row['first_name']} ({row['assessment_date']})": row["id"]
                for _, row in df.iterrows()
            }
            selected_label = st.selectbox("Select Resident to Update:", list(resident_options.keys()))
            record_id = resident_options[selected_label]
            selected_row = df[df["id"] == record_id].iloc[0]

            with st.form("edit_resident_form"):
                e_lname = st.text_input("Last Name", value=selected_row["last_name"])
                e_fname = st.text_input("First Name", value=selected_row["first_name"])
                e_weight = st.number_input("Weight (kg)", value=float(selected_row["weight_kg"]), step=0.5)
                e_height = st.number_input("Height (cm)", value=float(selected_row["height_cm"]), step=0.5)
                e_action = st.text_input("Action Taken", value=selected_row["action_taken"])

                if st.form_submit_button("Update Resident Record"):
                    new_bmi = calculate_bmi(e_weight, e_height)
                    new_bmi_cat = classify_bmi(new_bmi)

                    conn = sqlite3.connect("philpen_palo.db")
                    c = conn.cursor()
                    c.execute(
                        """
                        UPDATE assessments SET last_name=?, first_name=?, weight_kg=?, height_cm=?, bmi=?, bmi_class=?, action_taken=?
                        WHERE id=?
                    """,
                        (e_lname, e_fname, e_weight, e_height, new_bmi, new_bmi_cat, e_action, record_id),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Record updated successfully!")
                    st.rerun()

else:
    st.subheader(f"{nav_program} Module")
    st.info(f"The **{nav_program}** module is scheduled for data integration.")
