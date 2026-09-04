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
            assessor_name TEXT,
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
    # Ensure assessor_name column exists for legacy database files
    c.execute("PRAGMA table_info(assessments)")
    columns = [column[1] for column in c.fetchall()]
    if "assessor_name" not in columns:
        c.execute("ALTER TABLE assessments ADD COLUMN assessor_name TEXT")

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
# COMMON MEDICATIONS LIST
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
# HELPER CALCULATIONS & BP PARSING
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


def parse_bp(bp_str):
    if not bp_str or "/" not in bp_str:
        return None, None
    try:
        parts = bp_str.strip().split("/")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None, None


def calculate_average_bp(bp1, bp2, bp3):
    readings = [parse_bp(bp1), parse_bp(bp2), parse_bp(bp3)]
    valid_sbps = [s for s, d in readings if s is not None]
    valid_dbps = [d for s, d in readings if d is not None]

    if not valid_sbps:
        return "N/A", 120

    avg_sbp = round(sum(valid_sbps) / len(valid_sbps))
    avg_dbp = round(sum(valid_dbps) / len(valid_dbps)) if valid_dbps else 80
    return f"{avg_sbp}/{avg_dbp}", avg_sbp


def calculate_cvd_risk(age, sex, smoker, sbp, bmi, diabetes):
    if diabetes == "Meron" or sbp >= 160 or bmi >= 25.0:
        if age >= 60 or sbp >= 160:
            return "High", "20% to <30%", "#f43f5e"
        return "Medium", "10% to <20%", "#fbbf24"
    elif smoker == "Oo" or sbp >= 140:
        return "Mild", "5% to <10%", "#38bdf8"
    return "Low", "<5%", "#34d399"


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
# STREAMLIT CONFIG & LOW-GLARE DARK CHARCOAL STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="e-FHSIS | Palo, Leyte Portal", layout="wide", page_icon="🏥")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Base Dark Canvas */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }

    /* Standard Labels & Typography */
    p, span, label, h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stMarkdown *,
    div[role="radiogroup"] label,
    div[role="group"] label,
    [data-testid="stWidgetLabel"] * {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* Slate Input Cards */
    input, textarea, select,
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    input, textarea {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-weight: 600 !important;
    }

    /* Datepicker Styling */
    .stDateInput input,
    div[data-baseweb="datepicker"] input,
    div[data-baseweb="datepicker"] > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-weight: 600 !important;
    }

    /* Menus & Popovers */
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[role="listbox"] *,
    div[role="dialog"] * {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }

    /* Multiselect Badge Tags */
    span[data-baseweb="tag"] {
        background-color: #312e81 !important;
        color: #e0e7ff !important;
        border: 1px solid #4338ca !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] * {
        color: #e0e7ff !important;
    }

    /* Header Banner Gradient */
    .header-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        padding: 22px 28px;
        border-radius: 12px;
        color: #ffffff !important;
        margin-bottom: 25px;
    }
    .header-banner h1 {
        color: #f8fafc !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }
    .header-banner p {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        margin-top: 4px !important;
    }

    /* Dashboard KPI Containers */
    .kpi-card {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 18px !important;
    }
    .kpi-label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .kpi-value {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin-top: 4px !important;
    }
    .kpi-subtext {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        color: #818cf8 !important;
    }

    /* Flagged Alert Banner */
    .flag-red-card {
        background-color: #2a1215 !important;
        border: 1px solid #991b1b !important;
        border-left: 6px solid #f43f5e !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
    }

    /* Buttons */
    .stButton > button {
        background: #4f46e5 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
    }
    .stButton > button:hover {
        background: #4338ca !important;
        color: #ffffff !important;
    }

    /* Navigation Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }

    .dev-credit {
        font-size: 0.82rem;
        color: #94a3b8;
        border-top: 1px solid #334155;
        padding-top: 10px;
        margin-top: 10px;
    }
    .dev-credit strong {
        color: #818cf8;
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
# SIDEBAR NAVIGATION & DEVELOPER CREDIT
# ---------------------------------------------------------
st.sidebar.markdown(f"### 📍 **Barangay {st.session_state['user_brgy']}**")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.rerun()

# Lead Developer Attribution
st.sidebar.markdown(
    """
    <div class="dev-credit">
        👨‍⚕️ <strong>Lead Developer:</strong><br>
        <span style="color: #f8fafc; font-weight: 600;">Jan Art A. Serna, RMT</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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

# Sidebar Form Progress Placeholder
sidebar_progress_box = st.sidebar.empty()

# Fetch Barangay Dataset
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
                    <div class="kpi-value" style="color: #f43f5e;">{high_risk}</div>
                    <div class="kpi-subtext">Needs Urgent Care</div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Diabetic Cases</div>
                    <div class="kpi-value" style="color: #fbbf24;">{diabetic_ct}</div>
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
                    <div class="kpi-value" style="color: #38bdf8;">{hypertensive_ct}</div>
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
                    <div class="kpi-value" style="color: #a78bfa;">{rhu_ref_ct}</div>
                    <div class="kpi-subtext">Physician Care</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### **CVD Risk Stratification Breakdown**")
            risk_counts = df["risk_level"].value_counts()
            st.bar_chart(risk_counts, color="#6366f1")

        with chart_col2:
            st.markdown("#### **Demographics: Age Group & Sex Distribution**")
            bins = [0, 19, 30, 45, 64, 120]
            labels = ["<20", "20-29", "30-44", "45-64", "65+"]
            df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
            age_sex_df = pd.crosstab(df["age_group"], df["sex"])
            st.line_chart(age_sex_df)

        st.markdown("---")

        st.markdown("#### **High-Risk Patients Requiring Immediate Medical Intervention**")
        high_risk_df = df[df["risk_level"] == "High"][
            ["id", "last_name", "first_name", "age", "sex", "zone", "bp_avg", "has_diabetes", "action_taken", "assessor_name"]
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

    st.markdown("**1. General & Assessor Information**")
    col0_a, col0_b = st.columns(2)
    with col0_a:
        assessor_name = st.text_input("Pangalan ng BHW na Nag-assess (Assessor Name)*", key="p_assessor")
    with col0_b:
        assessment_date = st.date_input("Date of Assessment*", datetime.date.today(), key="p_date")

    col1, col2, col3 = st.columns(3)
    with col1:
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

    # DOUBLE ENTRY CHECK
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

    st.markdown("**3. Medical History & Specific Medications**")
    col_diab, col_htn = st.columns(2)

    with col_diab:
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"], key="p_diab")
        diabetes_meds_selected = []
        if has_diabetes == "Meron":
            diabetes_meds_selected = st.multiselect(
                "Ano ang iniinom mong gamot para sa Diabetes? (Select all that apply)*",
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
                "Ano ang iniinom mong gamot para sa Hypertension? (Select all that apply)*",
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

    st.markdown("**4. Blood Pressure Screening (Up to 3 Readings Allowed)**")
    bp_c1, bp_c2, bp_c3 = st.columns(3)
    with bp_c1:
        bp1 = st.text_input("Unang Blood Pressure (BP 1)* e.g., 120/80", key="p_bp1")
    with bp_c2:
        bp2 = st.text_input("Pangalawang Blood Pressure (BP 2 - Optional)", key="p_bp2")
    with bp_c3:
        bp3 = st.text_input("Pangatlong Blood Pressure (BP 3 - Optional)", key="p_bp3")

    bp_avg, sbp_for_calc = calculate_average_bp(bp1, bp2, bp3)
    if bp1:
        st.success(f"**Average Computed BP:** {bp_avg}")

    st.markdown("**5. Lifestyle & Risk Stratification**")
    smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo"], key="p_smoke")
    drinker = st.radio("Ikaw ba ay binge drinker?*", ["Hindi", "Oo"], key="p_drink")
    exercise = st.radio("Nakakapag-ehersisyo ka ba 150 mins/week?*", ["Oo", "Hindi"], key="p_exer")
    healthy_diet = st.radio("Nakakakain ng 5 platitong gulay/prutas araw-araw?*", ["Oo", "Hindi"], key="p_diet")

    risk_level, risk_pct, risk_color = calculate_cvd_risk(age, sex, smoker, sbp_for_calc, bmi, has_diabetes)
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

    # Calculate Sidebar Progress Tracker
    required_checks = [
        bool(assessor_name.strip()),
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

    # Sidebar Progress Bar Render
    with sidebar_progress_box.container():
        st.markdown("---")
        st.markdown("📋 **Form Completion Progress:**")
        st.progress(progress_pct / 100)
        st.caption(f"`{completed_fields}/{total_required}` Required Fields ({progress_pct}%)")

    if st.button("Save Assessment Record"):
        if is_duplicate:
            st.error(f"⛔ CANNOT SAVE RECORD: {first_name} {last_name} has already been assessed for {assessment_year}!")
        elif completed_fields < total_required:
            st.error("Paki-kumpleto ang lahat ng mandatory fields (*) kasama ang Pangalan ng BHW bago i-save!")
        else:
            conn = sqlite3.connect("philpen_palo.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO assessments (
                    assessment_date, assessor_name, last_name, first_name, middle_name, zone, barangay,
                    birthday, age, sex, weight_kg, height_cm, bmi, bmi_class, waist_cm,
                    waist_risk, has_diabetes, diabetes_meds, has_hypertension, hypertension_meds,
                    high_cholesterol, history_cvd_stroke, history_heart_attack, history_kidney,
                    family_history, bp_1, bp_2, bp_3, bp_avg, is_smoker, is_binge_drinker,
                    is_exercising, eats_healthy, risk_level, action_taken
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    str(assessment_date),
                    assessor_name,
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
        ["📋 Master Records Data Table", "📊 Visual Analytics & Chronic Rosters", "✏️ Edit Resident Record"]
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
            total_count = len(df)
            st.markdown("#### 📈 **Barangay Epidemiological Overview**")

            m1, m2, m3, m4, m5 = st.columns(5)
            diab_df = df[df["has_diabetes"] == "Meron"]
            htn_df = df[df["has_hypertension"] == "Meron"]
            diab_cnt = len(diab_df)
            htn_cnt = len(htn_df)
            high_risk_cnt = len(df[df["risk_level"] == "High"])
            smoker_cnt = len(df[df["is_smoker"] == "Oo"])
            obese_cnt = len(df[df["bmi_class"].str.contains("OBESITY", na=False)])

            with m1:
                st.metric("Total Population Screened", total_count)
            with m2:
                st.metric("High CVD Risk", high_risk_cnt, delta=f"{round((high_risk_cnt/total_count)*100, 1)}%")
            with m3:
                st.metric("Diabetic Cases", diab_cnt, delta=f"{round((diab_cnt/total_count)*100, 1)}%")
            with m4:
                st.metric("Hypertensive Cases", htn_cnt, delta=f"{round((htn_cnt/total_count)*100, 1)}%")
            with m5:
                st.metric("Obesity Rate", obese_cnt, delta=f"{round((obese_cnt/total_count)*100, 1)}%")

            st.markdown("---")

            # ---------------------------------------------------------
            # SPECIFIC LIST OF DIABETIC & HYPERTENSIVE PATIENTS
            # ---------------------------------------------------------
            st.markdown("### 🩺 **Diabetic and Hypertensive Resident Rosters**")
            roster_col1, roster_col2 = st.columns(2)

            with roster_col1:
                st.markdown("#### 🩸 **List of Diabetic Residents**")
                if not diab_df.empty:
                    diab_list = diab_df[
                        [
                            "id",
                            "last_name",
                            "first_name",
                            "age",
                            "zone",
                            "diabetes_meds",
                            "bp_avg",
                            "action_taken",
                            "assessor_name",
                        ]
                    ]
                    st.dataframe(diab_list, use_container_width=True)
                else:
                    st.success("No diabetic residents recorded.")

            with roster_col2:
                st.markdown("#### 🫀 **List of Hypertensive Residents**")
                if not htn_df.empty:
                    htn_list = htn_df[
                        [
                            "id",
                            "last_name",
                            "first_name",
                            "age",
                            "zone",
                            "hypertension_meds",
                            "bp_avg",
                            "action_taken",
                            "assessor_name",
                        ]
                    ]
                    st.dataframe(htn_list, use_container_width=True)
                else:
                    st.success("No hypertensive residents recorded.")

            st.markdown("---")

            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.markdown("##### 🎯 **CVD Risk Level Distribution**")
                risk_summary = df["risk_level"].value_counts().reset_index()
                risk_summary.columns = ["Risk Level", "Count"]
                st.bar_chart(risk_summary.set_index("Risk Level"), color="#6366f1")

                st.markdown("##### ⚖️ **Body Mass Index (BMI) Categories**")
                bmi_summary = df["bmi_class"].value_counts().reset_index()
                bmi_summary.columns = ["BMI Category", "Count"]
                st.bar_chart(bmi_summary.set_index("BMI Category"), color="#38bdf8")

            with col_graph2:
                st.markdown("##### 👥 **Age & Sex Distribution Visual**")
                bins = [0, 19, 30, 45, 64, 120]
                labels = ["< 20", "20-29", "30-44", "45-64", "65+"]
                df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
                age_sex_crosstab = pd.crosstab(df["age_group"], df["sex"])
                st.area_chart(age_sex_crosstab)

                st.markdown("##### 🚬 **Lifestyle Risk Factors Profile**")
                lifestyle_data = pd.DataFrame(
                    {
                        "Risk Factor": ["Smoker", "Binge Drinker", "Inadequate Exercise", "Unhealthy Diet"],
                        "Count": [
                            len(df[df["is_smoker"] == "Oo"]),
                            len(df[df["is_binge_drinker"] == "Oo"]),
                            len(df[df["is_exercising"] == "Hindi"]),
                            len(df[df["eats_healthy"] == "Hindi"]),
                        ],
                    }
                )
                st.bar_chart(lifestyle_data.set_index("Risk Factor"), color="#f43f5e")

    with tab_edit:
        if df.empty:
            st.info("No records available to edit.")
        else:
            resident_options = {
                f"ID {row['id']}: {row['last_name']}, {row['first_name']} ({row['assessment_date']})": row["id"]
                for _, row in df.iterrows()
            }
            selected_label = st.selectbox("Select Resident Record to Edit:", list(resident_options.keys()))
            record_id = resident_options[selected_label]
            rec = df[df["id"] == record_id].iloc[0]

            st.markdown("---")
            st.markdown(f"#### ✏️ **Complete Record Field Edit — Resident ID #{record_id}**")

            with st.form("edit_full_resident_form"):
                st.markdown("**1. General & Assessor Information**")
                e_assessor_name = st.text_input("Pangalan ng BHW / Assessor", value=str(rec.get("assessor_name", "")))

                ec1, ec2, ec3 = st.columns(3)

                try:
                    curr_ass_date = datetime.datetime.strptime(str(rec["assessment_date"]), "%Y-%m-%d").date()
                except ValueError:
                    curr_ass_date = datetime.date.today()

                try:
                    curr_dob = datetime.datetime.strptime(str(rec["birthday"]), "%Y-%m-%d").date()
                except ValueError:
                    curr_dob = datetime.date(1990, 1, 1)

                with ec1:
                    e_assessment_date = st.date_input("Assessment Date", value=curr_ass_date)
                    e_last_name = st.text_input("Apilido (Last Name)", value=str(rec["last_name"]))
                with ec2:
                    e_first_name = st.text_input("Pangalan (Given Name)", value=str(rec["first_name"]))
                    e_middle_name = st.text_input("Gitnang Pangalan (Middle Name)", value=str(rec["middle_name"] or ""))
                with ec3:
                    e_zone = st.text_input("Zone / Purok", value=str(rec["zone"]))
                    e_barangay = st.text_input("Barangay", value=str(rec["barangay"]), disabled=True)

                ec_dob, ec_sex = st.columns(2)
                with ec_dob:
                    e_dob = st.date_input("Birthday", value=curr_dob, min_value=datetime.date(1920, 1, 1))
                    e_age = calculate_age(e_dob)
                    st.caption(f"Calculated Age: {e_age} years old")
                with ec_sex:
                    sex_options = ["Male", "Female", "Other"]
                    sex_idx = sex_options.index(rec["sex"]) if rec["sex"] in sex_options else 0
                    e_sex = st.radio("Sex", sex_options, index=sex_idx)

                st.markdown("**2. Body Measurements**")
                ew_col, eh_col, ewaist_col = st.columns(3)
                with ew_col:
                    e_weight = st.number_input("Weight (kg)", value=float(rec["weight_kg"]), min_value=0.0, step=0.5)
                with eh_col:
                    e_height = st.number_input("Height (cm)", value=float(rec["height_cm"]), min_value=0.0, step=0.5)
                with ewaist_col:
                    e_waist = st.number_input("Waist (cm)", value=float(rec["waist_cm"]), min_value=0.0, step=0.5)

                st.markdown("**3. Medical History & Medications**")
                ediab_col, ehtn_col = st.columns(2)

                with ediab_col:
                    diab_options = ["Wala", "Meron", "Diri ak maaram"]
                    diab_idx = diab_options.index(rec["has_diabetes"]) if rec["has_diabetes"] in diab_options else 0
                    e_has_diabetes = st.selectbox("May Diabetes?", diab_options, index=diab_idx)

                    curr_diab_meds = [m.strip() for m in str(rec["diabetes_meds"]).split(",") if m.strip()]
                    e_diab_meds = st.multiselect(
                        "Diabetes Medications", options=DIABETES_MEDICATIONS, default=[m for m in curr_diab_meds if m in DIABETES_MEDICATIONS]
                    )

                with ehtn_col:
                    htn_options = ["Wala", "Meron", "Diri ak maaram"]
                    htn_idx = htn_options.index(rec["has_hypertension"]) if rec["has_hypertension"] in htn_options else 0
                    e_has_htn = st.selectbox("May Hypertension?", htn_options, index=htn_idx)

                    curr_htn_meds = [m.strip() for m in str(rec["hypertension_meds"]).split(",") if m.strip()]
                    e_htn_meds = st.multiselect(
                        "Hypertension Medications", options=HYPERTENSION_MEDICATIONS, default=[m for m in curr_htn_meds if m in HYPERTENSION_MEDICATIONS]
                    )

                chol_options = ["Hindi", "Oo", "Diri ak maaram"]
                chol_idx = chol_options.index(rec["high_cholesterol"]) if rec["high_cholesterol"] in chol_options else 0
                e_cholesterol = st.selectbox("High Cholesterol?", chol_options, index=chol_idx)

                st.write("Medical Diagnoses:")
                e_cvd_stroke = st.checkbox("History of CVD (Stroke)", value=bool(rec["history_cvd_stroke"]))
                e_heart_attack = st.checkbox("History of Heart attack", value=bool(rec["history_heart_attack"]))
                e_kidney_prob = st.checkbox("Chronic Kidney Problem", value=bool(rec["history_kidney"]))

                fam_options = ["Wala", "Meron"]
                fam_idx = fam_options.index(rec["family_history"]) if rec["family_history"] in fam_options else 0
                e_fam_history = st.selectbox("Family History of CVD", fam_options, index=fam_idx)

                st.markdown("**4. Blood Pressure Screening (3 Readings)**")
                ebp1_col, ebp2_col, ebp3_col = st.columns(3)
                with ebp1_col:
                    e_bp1 = st.text_input("BP Reading 1", value=str(rec["bp_1"]))
                with ebp2_col:
                    e_bp2 = st.text_input("BP Reading 2", value=str(rec["bp_2"] or ""))
                with ebp3_col:
                    e_bp3 = st.text_input("BP Reading 3", value=str(rec["bp_3"] or ""))

                st.markdown("**5. Lifestyle Factors & Action Taken**")
                els1, els2, els3, els4 = st.columns(4)
                yn_opts = ["Hindi", "Oo"]
                ny_opts = ["Oo", "Hindi"]

                with els1:
                    e_smoker = st.radio("Smoker", yn_opts, index=0 if rec["is_smoker"] == "Hindi" else 1)
                with els2:
                    e_drinker = st.radio("Binge Drinker", yn_opts, index=0 if rec["is_binge_drinker"] == "Hindi" else 1)
                with els3:
                    e_exercise = st.radio("Exercises 150m/wk", ny_opts, index=0 if rec["is_exercising"] == "Oo" else 1)
                with els4:
                    e_healthy_diet = st.radio("Eats Healthy", ny_opts, index=0 if rec["eats_healthy"] == "Oo" else 1)

                action_list = [
                    "Advise sa diet at lifestyle (Counselling)",
                    "Ni-refer kay midwife para sa kumpletong assessment",
                    "Ni-refer sa RHU Physician",
                    "Urgent referral sa Ospital / Physician",
                    "Nirefer sa RHU/Ospital pero tumanggi",
                ]
                act_idx = action_list.index(rec["action_taken"]) if rec["action_taken"] in action_list else 0
                e_action = st.selectbox("Action Taken", action_list, index=act_idx)

                st.markdown("---")
                save_changes = st.form_submit_button("💾 Save All Changes to Resident Record")

                if save_changes:
                    new_bmi = calculate_bmi(e_weight, e_height)
                    new_bmi_cat = classify_bmi(new_bmi)
                    new_waist_risk = classify_waist(e_sex, e_waist)

                    new_bp_avg, e_systolic = calculate_average_bp(e_bp1, e_bp2, e_bp3)

                    new_risk_level, _, _ = calculate_cvd_risk(e_age, e_sex, e_smoker, e_systolic, new_bmi, e_has_diabetes)
                    e_diab_meds_str = ", ".join(e_diab_meds) if e_diab_meds else "None"
                    e_htn_meds_str = ", ".join(e_htn_meds) if e_htn_meds else "None"

                    conn = sqlite3.connect("philpen_palo.db")
                    c = conn.cursor()
                    c.execute(
                        """
                        UPDATE assessments SET
                            assessment_date=?, assessor_name=?, last_name=?, first_name=?, middle_name=?, zone=?,
                            birthday=?, age=?, sex=?, weight_kg=?, height_cm=?, bmi=?, bmi_class=?,
                            waist_cm=?, waist_risk=?, has_diabetes=?, diabetes_meds=?, has_hypertension=?,
                            hypertension_meds=?, high_cholesterol=?, history_cvd_stroke=?, history_heart_attack=?,
                            history_kidney=?, family_history=?, bp_1=?, bp_2=?, bp_3=?, bp_avg=?,
                            is_smoker=?, is_binge_drinker=?, is_exercising=?, eats_healthy=?,
                            risk_level=?, action_taken=?
                        WHERE id=?
                    """,
                        (
                            str(e_assessment_date),
                            e_assessor_name,
                            e_last_name,
                            e_first_name,
                            e_middle_name,
                            e_zone,
                            str(e_dob),
                            e_age,
                            e_sex,
                            e_weight,
                            e_height,
                            new_bmi,
                            new_bmi_cat,
                            e_waist,
                            new_waist_risk,
                            e_has_diabetes,
                            e_diab_meds_str,
                            e_has_htn,
                            e_htn_meds_str,
                            e_cholesterol,
                            int(e_cvd_stroke),
                            int(e_heart_attack),
                            int(e_kidney_prob),
                            e_fam_history,
                            e_bp1,
                            e_bp2,
                            e_bp3,
                            new_bp_avg,
                            e_smoker,
                            e_drinker,
                            e_exercise,
                            e_healthy_diet,
                            new_risk_level,
                            e_action,
                            record_id,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("All record details updated successfully!")
                    st.rerun()

else:
    st.subheader(f"{nav_program} Module")
    st.info(f"The **{nav_program}** module is scheduled for data integration.")
