import datetime
import sqlite3
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# SMS NOTIFICATION INTEGRATION FUNCTION
# ---------------------------------------------------------
def send_sms_notification(contact_number, message):
    """
    Sends SMS notification to resident using an SMS Gateway API (e.g., Semaphore / Twilio).
    For live deployment, uncomment the requests call and add your API key.
    """
    if not contact_number or len(str(contact_number).strip()) < 10:
        return False, "Invalid contact number."
    
    # --- SEMAPHORE API INTEGRATION EXAMPLE (Philippines) ---
    # import requests
    # api_key = "YOUR_SEMAPHORE_API_KEY"
    # payload = {'apikey': api_key, 'number': contact_number, 'message': message, 'sendername': 'PHILPEN'}
    # response = requests.post('https://api.semaphore.co/api/v4/messages', data=payload)
    # return response.status_code == 200, response.text
    
    # Simulated SMS success for demonstration:
    print(f"[SMS SENT TO {contact_number}]: {message}")
    return True, "SMS simulated successfully."

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
            contact_number TEXT,
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
            takes_diabetes_meds TEXT,
            diabetes_meds TEXT,
            has_hypertension TEXT,
            takes_htn_meds TEXT,
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

    # Database Migration Check for Columns
    c.execute("PRAGMA table_info(assessments)")
    columns = [column[1] for column in c.fetchall()]
    if "assessor_name" not in columns:
        c.execute("ALTER TABLE assessments ADD COLUMN assessor_name TEXT")
    if "takes_diabetes_meds" not in columns:
        c.execute("ALTER TABLE assessments ADD COLUMN takes_diabetes_meds TEXT")
    if "takes_htn_meds" not in columns:
        c.execute("ALTER TABLE assessments ADD COLUMN takes_htn_meds TEXT")
    if "contact_number" not in columns:
        c.execute("ALTER TABLE assessments ADD COLUMN contact_number TEXT")

    conn.commit()
    conn.close()


init_db()

# ---------------------------------------------------------
# MUNICIPAL & BARANGAY CREDENTIALS
# ---------------------------------------------------------
BARANGAY_CREDENTIALS = {
    "paloadmin": "palo2026",  # Municipal Admin Credential
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

ONLY_BARANGAYS = [b for b in BARANGAY_CREDENTIALS.keys() if b != "paloadmin"]

# ---------------------------------------------------------
# MEDICATIONS LISTS
# ---------------------------------------------------------
HYPERTENSION_MEDICATIONS = [
    "Losartan 50mg tab",
    "Amlodipine 5mg/10mg tab",
    "Telmisartan 40mg/80mg tab",
    "Captopril 25mg tab",
    "Metoprolol 50mg/100mg tab",
    "Enalapril 5mg/20mg tab",
    "Hydrochlorothiazide (HCTZ) 12.5mg/25mg",
    "Carvedilol 6.25mg/12.5mg tab",
    "Iba pa (Others)",
]

DIABETES_MEDICATIONS = [
    "Metformin 500mg tab",
    "Gliclazide 30mg/80mg tab",
    "Glimepiride 2mg/4mg tab",
    "Insulin Human NPH / Regular",
    "Sitagliptin 50mg/100mg tab",
    "Empagliflozin 10mg/25mg tab",
    "Iba pa (Others)",
]

# ---------------------------------------------------------
# HELPER CALCULATIONS
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
    if (diabetes == "Meron" and sbp >= 160) or (sbp >= 180) or (diabetes == "Meron" and age >= 60 and smoker == "Oo"):
        return "Very High", "≥30%", "#7f1d1d", "#ffffff", "Urgent referral to Physician/ Hospital"
    elif diabetes == "Meron" or sbp >= 160 or (bmi >= 25.0 and age >= 60):
        if age >= 60 or sbp >= 160:
            return "High", "20% to <30%", "#dc2626", "#ffffff", "Urgent referral to Physician/ Hospital"
        return "Medium", "10% to <20%", "#ea580c", "#ffffff", "Refer to RHU Physician"
    elif smoker == "Oo" or sbp >= 140 or bmi >= 25.0:
        return "Mild", "5% to <10%", "#eab308", "#000000", "Refer to Midwife"
    return "Low", "<5%", "#16a34a", "#ffffff", "Counselling only"


def check_annual_duplicate(first_name, last_name, dob, year, exclude_id=None):
    if not first_name.strip() or not last_name.strip():
        return False, None

    conn = sqlite3.connect("philpen_palo.db")
    c = conn.cursor()

    query = """
        SELECT id, assessment_date, first_name, last_name FROM assessments 
        WHERE birthday = ?
          AND strftime('%Y', assessment_date) = ?
    """
    params = [str(dob), str(year)]

    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)

    c.execute(query, params)
    records = c.fetchall()
    conn.close()

    input_tokens = sorted(f"{first_name} {last_name}".lower().split())

    for r in records:
        rec_id, ass_date, db_fn, db_ln = r
        db_tokens = sorted(f"{db_fn} {db_ln}".lower().split())
        if input_tokens == db_tokens:
            return True, ass_date

    return False, None


def render_modern_table_html(title, headers, rows):
    header_html = "".join([f'<th style="padding: 10px; border-bottom: 2px solid #334155; color: #818cf8; font-weight: 600; text-align: left;">{h}</th>' for h in headers])
    rows_html = ""
    for row in rows:
        cells = "".join([f'<td style="padding: 10px; border-bottom: 1px solid #334155; text-align: left;">{cell}</td>' for cell in row])
        rows_html += f"<tr>{cells}</tr>"

    html = f"""
    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
        <h5 style="color: #f8fafc; font-weight: 700; margin-top: 0; margin-bottom: 12px; text-align: left;">{title}</h5>
        <table style="width: 100%; border-collapse: collapse; text-align: left; color: #f8fafc; font-size: 0.9rem;">
            <thead>
                <tr style="background-color: #0f172a;">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return html


# ---------------------------------------------------------
# STREAMLIT CONFIG & LOW-GLARE DARK CHARCOAL STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="TEKI Portal", layout="wide", page_icon="🏥")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        text-align: left !important;
    }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }

    p, span, label, h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stMarkdown *,
    div[role="radiogroup"] label,
    div[role="group"] label,
    [data-testid="stWidgetLabel"] * {
        color: #f8fafc !important;
        font-weight: 500 !important;
        text-align: left !important;
    }

    input, textarea, select,
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        text-align: left !important;
    }

    input, textarea {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-weight: 600 !important;
    }

    .stDateInput input,
    div[data-baseweb="datepicker"] input,
    div[data-baseweb="datepicker"] > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[role="listbox"] *,
    div[role="dialog"] * {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        text-align: left !important;
    }

    span[data-baseweb="tag"] {
        background-color: #312e81 !important;
        color: #e0e7ff !important;
        border: 1px solid #4338ca !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] * {
        color: #e0e7ff !important;
    }

    .header-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        padding: 22px 28px;
        border-radius: 12px;
        color: #ffffff !important;
        margin-bottom: 25px;
        text-align: left !important;
    }
    .header-banner h1 {
        color: #f8fafc !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        text-align: left !important;
    }
    .header-banner p {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        margin-top: 4px !important;
        text-align: left !important;
    }

    .kpi-card {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 18px !important;
        text-align: left !important;
    }
    .kpi-label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        text-align: left !important;
    }
    .kpi-value {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin-top: 4px !important;
        text-align: left !important;
    }
    .kpi-subtext {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        color: #818cf8 !important;
        text-align: left !important;
    }

    .flag-red-card {
        background-color: #2a1215 !important;
        border: 1px solid #991b1b !important;
        border-left: 6px solid #f43f5e !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
        text-align: left !important;
    }

    /* Streamlit buttons strict left alignment & container structure */
    .stButton > button {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
        width: 100% !important;
        font-size: 0.95rem !important;
        padding: 12px 18px !important;
        border-radius: 8px !important;
    }

    /* Force all child elements (p, div, span) inside stButton to align strictly to the left */
    .stButton > button * {
        text-align: left !important;
        justify-content: flex-start !important;
    }

    .stButton > button p {
        display: block !important;
        text-align: left !important;
        font-size: 0.98rem !important;
        line-height: 1.5 !important;
        margin: 0 !important;
        width: 100% !important;
    }

    /* ENLARGE COLOR INDICATOR TO PENNY SIZE (~28px) STRICTLY ON THE LEFT */
    .stButton > button p::first-letter {
        font-size: 1.8rem !important; /* Penny size scale (~28px diameter) */
        line-height: 1 !important;
        margin-right: 10px !important;
        vertical-align: -2px !important;
        display: inline-block !important;
    }

    /* Selected option box highlight styling */
    .stButton > button[kind="primary"] {
        background: #312e81 !important;
        border: 2px solid #6366f1 !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.4) !important;
        font-weight: 600 !important;
    }

    /* Unselected option box styling */
    .stButton > button[kind="secondary"] {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f8fafc !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #334155 !important;
        border-color: #475569 !important;
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
        text-align: left !important;
    }

    .dev-credit {
        font-size: 0.82rem;
        color: #94a3b8;
        border-top: 1px solid #334155;
        padding-top: 10px;
        margin-top: 10px;
        text-align: left !important;
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
        <h1>TEKI: Technology-Enabled Knowledge and Information System</h1>
        <p><i>An Integrated Digital Platform for Barangay Health Program Recording and Reporting</i></p>
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
    st.subheader("TEKI Portal Login")

    with st.form("login_form"):
        username = st.selectbox("Select Account / Barangay (Username)", list(BARANGAY_CREDENTIALS.keys()))
        password = st.text_input("Access Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if BARANGAY_CREDENTIALS.get(username) == password:
                st.session_state["authenticated"] = True
                st.session_state["user_brgy"] = username
                st.rerun()
            else:
                st.error("Incorrect password for the selected account.")
    st.stop()

is_admin = (st.session_state["user_brgy"] == "paloadmin")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & MAIN MODULE HIERARCHY
# ---------------------------------------------------------
if is_admin:
    st.sidebar.markdown("### 🏛️ **Municipal Administrator**")
    st.sidebar.caption("Palo, Leyte Health System (All Barangays)")
else:
    st.sidebar.markdown(f"### 📍 **Barangay {st.session_state['user_brgy']}**")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.rerun()

st.sidebar.markdown(
    """
    <div class="dev-credit">
        👨‍⚕️ <strong>Lead Developer:</strong><br>
        <span style="color: #f8fafc; font-weight: 600;">Jan Art A. Serna, RMT</span><br><br>
        🎓 <strong>Capstone Project Proposed by:</strong><br>
        <span style="color: #f8fafc; font-weight: 600;">Lesterel C. Kidit, RM, RN, MD</span><br>
        <span style="color: #f8fafc; font-weight: 600;">Nova Nizza B. Dacayanan, RM, RN, MD</span><br>
        <span style="color: #f8fafc; font-weight: 600;">James O. Peconcillo, RM, RN, MD</span><br>
        <span style="color: #818cf8; font-size: 0.8rem;">University of the Philippines Manila-SHS</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation Menu**")

# MAIN MODULE NAVIGATION WITH PHILPEN PROGRAM & SUB-MODULES
main_nav = st.sidebar.radio(
    "Select Program Module:",
    [
        " Executive Dashboard",
        "PhilPEN Program",
        "   └ 🩺 PhilPEN Assessment Form",
        "   └ 📊 PhilPEN Database and Analytics",
        "Nutritional Status (0-59 mos)",
        "Expanded Program on Immunization",
        "Maternal Care",
        "Schistosomiasis",
        "NTP",
        "Mental Health Program",
    ],
)

sidebar_progress_box = st.sidebar.empty()

# Fetch Dataset
conn = sqlite3.connect("philpen_palo.db")
if is_admin:
    df = pd.read_sql_query("SELECT * FROM assessments", conn)
else:
    df = pd.read_sql_query(
        "SELECT * FROM assessments WHERE barangay = ?",
        conn,
        params=(st.session_state["user_brgy"],),
    )
conn.close()

portal_location_title = "Municipality of Palo (All Barangays Overview)" if is_admin else f"Barangay {st.session_state['user_brgy']}"

# ---------------------------------------------------------
# MODULE 1: EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if main_nav == " Executive Dashboard":
    st.subheader(f"Executive Health Dashboard — {portal_location_title}")
    
    # Executive Dashboard Title Requirement
    st.markdown("### 📋 **PhilPEN Risk Assessment Results**")

    if df.empty:
        st.info("No resident risk assessment records found. Complete assessments to generate real-time metrics.")
    else:
        total_assessed = len(df)
        high_risk = len(df[df["risk_level"].isin(["High", "Very High"])])
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
                    <div class="kpi-label">High/Very High Risk</div>
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
                    <div class="kpi-label">Diabetes Mellitus</div>
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
                    <div class="kpi-label">Hypertension</div>
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

        if is_admin:
            st.markdown("---")
            st.markdown("#### 🏛️ **Barangay Screening Performance Breakdown**")
            brgy_counts = df["barangay"].value_counts()
            st.bar_chart(brgy_counts, color="#38bdf8")

        st.markdown("---")

        st.markdown("#### **High & Very High Risk Patients Requiring Immediate Medical Intervention**")
        high_risk_df = df[df["risk_level"].isin(["High", "Very High"])][
            ["id", "barangay", "last_name", "first_name", "age", "sex", "zone", "contact_number", "bp_avg", "has_diabetes", "risk_level", "action_taken", "assessor_name"]
        ]
        if not high_risk_df.empty:
            st.dataframe(high_risk_df, use_container_width=True)
        else:
            st.success("No residents currently categorized as High or Very High CVD Risk.")

# ---------------------------------------------------------
# MODULE 2: PHILPEN PROGRAM - PHILPEN ASSESSMENT FORM
# ---------------------------------------------------------
elif main_nav in ["PhilPEN Program", "   └ 🩺 PhilPEN Assessment Form"]:
    st.subheader(f"PhilPEN Assessment Form — {portal_location_title}")

    st.markdown("**1. General & Assessor Information**")
    
    # Assessor & Date
    col0_a, col0_b = st.columns(2)
    with col0_a:
        assessor_name = st.text_input("Pangalan ng BHW / Assessor*", key="p_assessor")
    with col0_b:
        assessment_date = st.date_input("Date of Assessment*", datetime.date.today(), key="p_date")

    # ONE LINE: Apilido, Pangalan, Gitnang Pangalan
    col_lname, col_fname, col_mname = st.columns(3)
    with col_lname:
        last_name = st.text_input("Apilido (Last Name)*", key="p_lname")
    with col_fname:
        first_name = st.text_input("Pangalan (Given Name)*", key="p_fname")
    with col_mname:
        middle_name = st.text_input("Gitnang Pangalan (Middle Name)", key="p_mname")

    # ONE LINE: Zone/Purok, Barangay, Contact Number
    col_zone, col_brgy, col_contact = st.columns(3)
    with col_zone:
        zone = st.text_input("Zone / Purok*", key="p_zone")
    with col_brgy:
        if is_admin:
            target_barangay = st.selectbox("Barangay*", ONLY_BARANGAYS, key="p_brgy_select")
        else:
            target_barangay = st.text_input("Barangay", value=st.session_state["user_brgy"], disabled=True)
    with col_contact:
        contact_number = st.text_input("Contact Number (e.g. 09123456789)*", key="p_contact")

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

    # AGE VALIDATION FLAG (< 20 YEARS OLD)
    is_underage = age < 20
    if is_underage:
        st.markdown(
            f"""
            <div class="flag-red-card">
                <h4>🔴 FLAGGED AS INELIGIBLE AGE (UNDER 20 YEARS OLD)</h4>
                <p>
                    The calculated age is <strong>{age} years old</strong>. PhilPEN Risk Assessment protocol is strictly applicable for residents <strong>20 years old and above</strong>.<br>
                    ⚠️ <em>Policy restriction: Entry submission is disabled.</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    assessment_year = assessment_date.year
    is_duplicate, prev_date = check_annual_duplicate(first_name, last_name, dob, assessment_year)

    if is_duplicate:
        st.markdown(
            f"""
            <div class="flag-red-card">
                <h4>🔴 FLAGGED AS DOUBLE ENTRY (ANNUAL LIMIT EXCEEDED)</h4>
                <p>
                    A record for <strong>{first_name.upper()} {last_name.upper()}</strong> (DOB: {dob}) already exists for calendar year <strong>{assessment_year}</strong> (Assessed on <strong>{prev_date}</strong>).<br>
                    ⚠️ <em>Policy: Each resident can only undergo PhilPEN Assessment <u>once per calendar year</u>. Submission is disabled.</em>
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

    st.markdown("**3. Medical History & Medications Screening**")
    col_htn_sec, col_diab_sec = st.columns(2)

    with col_htn_sec:
        st.markdown("##### 🫀 **Hypertension Screening**")
        has_htn = st.selectbox("May ada ka ba High blood / Hypertension?*", ["Wala", "Meron", "Diri ak maaram"], key="p_htn")
        
        takes_htn_meds = st.radio(
            "May iniinom ka bang gamot para sa Hypertension?*",
            ["Wala", "Meron"],
            key="p_htn_meds_ask"
        )
        
        htn_meds_selected = []
        if takes_htn_meds == "Meron":
            htn_meds_selected = st.multiselect(
                "Ano ang iniinom mong gamot para sa Hypertension?",
                options=HYPERTENSION_MEDICATIONS,
                default=["Losartan 50mg tab"],
                key="p_htn_meds_multi"
            )
        htn_meds_str = ", ".join(htn_meds_selected) if htn_meds_selected else "Wala"

    with col_diab_sec:
        st.markdown("##### 🩸 **Diabetes Screening**")
        has_diabetes = st.selectbox("May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"], key="p_diab")
        
        takes_diabetes_meds = st.radio(
            "May gamot ka ba na iniinom para sa Diabetes?*",
            ["Wala", "Meron"],
            key="p_diab_meds_ask"
        )
        
        diabetes_meds_selected = []
        if takes_diabetes_meds == "Meron":
            diabetes_meds_selected = st.multiselect(
                "Ano ang iniinom mong gamot para sa Diabetes?",
                options=DIABETES_MEDICATIONS,
                default=["Metformin 500mg tab"],
                key="p_diab_meds_multi"
            )
        diabetes_meds_str = ", ".join(diabetes_meds_selected) if diabetes_meds_selected else "Wala"

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

    risk_level, risk_pct, risk_color, text_color, recommended_action = calculate_cvd_risk(age, sex, smoker, sbp_for_calc, bmi, has_diabetes)
    
    st.markdown(
        f"""
        <div style="background-color: {risk_color}; color: {text_color}; padding: 14px 20px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-align: left;">
            <span style="font-size: 1.15rem; color: {text_color} !important;">WHO/ISH Risk Assessment: <strong>{risk_level} Risk ({risk_pct})</strong></span><br>
            <span style="font-size: 0.95rem; color: {text_color} !important;">💡 Recommended Action: <strong>{recommended_action}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # MAP CALCULATED CVD RISK TO DEFAULT ACTION TAKEN
    action_mapping = {
        "Low": "Advise sa diet at lifestyle (Counselling)",
        "Mild": "Ni-refer kay midwife para sa kumpletong assessment",
        "Medium": "Ni-refer sa RHU Physician",
        "High": "Urgent referral sa Ospital / Physician",
        "Very High": "Urgent referral sa Ospital / Physician",
    }
    auto_default_action = action_mapping.get(risk_level, "Advise sa diet at lifestyle (Counselling)")

    # AUTO-SYNC ACTION WITH CALCULATED RISK LEVEL UNLESS OVERRIDDEN
    if "p_selected_action" not in st.session_state or st.session_state.get("p_last_risk") != risk_level:
        st.session_state["p_selected_action"] = auto_default_action
        st.session_state["p_last_risk"] = risk_level

    st.markdown("##### 🎯 **Action Taken: Click Option Box to Select**")
    st.caption("Click any colored option box below to select the Action Taken (Only 1 action can be chosen):")

    # FULL-WIDTH CLICKABLE OPTION BOXES WITH PENNY-SIZED DOTS (1.8rem / ~28px) STRICTLY ON LEFT
    indicator_options = [
        {
            "label": "Low Risk (<5%)",
            "dot": "🟢",
            "action": "Advise sa diet at lifestyle (Counselling)",
            "key": "btn_act_low_v",
            "desc": "Advise sa diet at lifestyle (Counselling)",
        },
        {
            "label": "Mild Risk (5% to <10%)",
            "dot": "🟡",
            "action": "Ni-refer kay midwife para sa kumpletong assessment",
            "key": "btn_act_mild_v",
            "desc": "Ni-refer kay midwife para sa kumpletong assessment",
        },
        {
            "label": "Medium Risk (10% to <20%)",
            "dot": "🟠",
            "action": "Ni-refer sa RHU Physician",
            "key": "btn_act_med_v",
            "desc": "Ni-refer sa RHU Physician",
        },
        {
            "label": "High Risk (20% to <30%)",
            "dot": "🔴",
            "action": "Urgent referral sa Ospital / Physician",
            "key": "btn_act_high_v",
            "desc": "Urgent referral sa Ospital / Physician",
        },
        {
            "label": "Very High Risk (≥30%)",
            "dot": "🔴",
            "action": "Urgent referral sa Ospital / Physician",
            "key": "btn_act_vhigh_v",
            "desc": "Urgent referral sa Ospital / Physician",
        },
        {
            "label": "Tumanggi / Patient Refusal",
            "dot": "⚪",
            "action": "Nirefer sa RHU/Ospital pero tumanggi",
            "key": "btn_act_refused_v",
            "desc": "Nirefer sa RHU/Ospital pero tumanggi",
        },
    ]

    for opt in indicator_options:
        is_active = (st.session_state.get("p_selected_action") == opt["action"])
        button_label = f"{opt['dot']} {opt['label']} — {opt['desc']}"
        btn_type = "primary" if is_active else "secondary"

        if st.button(button_label, key=opt["key"], use_container_width=True, type=btn_type):
            st.session_state["p_selected_action"] = opt["action"]
            st.rerun()

    action = st.session_state.get("p_selected_action", auto_default_action)

    st.markdown(
        f"""
        <div style="background-color: #1e293b; border: 2px solid #6366f1; border-radius: 8px; padding: 12px 18px; margin-top: 10px; margin-bottom: 20px; text-align: left;">
            <span style="color: #818cf8; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Selected Action Taken:</span><br>
            <strong style="color: #f8fafc; font-size: 1.1rem;">{action}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    required_checks = [
        bool(assessor_name.strip()),
        bool(last_name.strip()),
        bool(first_name.strip()),
        bool(zone.strip()),
        bool(contact_number.strip()),
        weight > 0,
        height > 0,
        waist > 0,
        bool(bp1.strip()),
        bool(action),
    ]

    completed_fields = sum(required_checks)
    total_required = len(required_checks)
    progress_pct = int((completed_fields / total_required) * 100)

    with sidebar_progress_box.container():
        st.markdown("---")
        st.markdown("📋 **Form Completion Progress:**")
        st.progress(progress_pct / 100)
        st.caption(f"`{completed_fields}/{total_required}` Required Fields ({progress_pct}%)")

    if st.button("Save Assessment Record"):
        if is_underage:
            st.error(f"⛔ CANNOT SAVE RECORD: Resident age is {age} years old. PhilPEN Assessment requires individuals to be 20 years old or older!")
        elif is_duplicate:
            st.error(f"⛔ CANNOT SAVE RECORD: A record for {first_name} {last_name} already exists for {assessment_year}!")
        elif completed_fields < total_required:
            st.error("Paki-kumpleto ang lahat ng mandatory fields (*) kasama ang Pangalan ng BHW at Contact Number bago i-save!")
        else:
            conn = sqlite3.connect("philpen_palo.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO assessments (
                    assessment_date, assessor_name, last_name, first_name, middle_name, zone, barangay, contact_number,
                    birthday, age, sex, weight_kg, height_cm, bmi, bmi_class, waist_cm,
                    waist_risk, has_diabetes, takes_diabetes_meds, diabetes_meds, has_hypertension, 
                    takes_htn_meds, hypertension_meds, high_cholesterol, history_cvd_stroke, 
                    history_heart_attack, history_kidney, family_history, bp_1, bp_2, bp_3, 
                    bp_avg, is_smoker, is_binge_drinker, is_exercising, eats_healthy, risk_level, action_taken
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    str(assessment_date),
                    assessor_name,
                    last_name,
                    first_name,
                    middle_name,
                    zone,
                    target_barangay,
                    contact_number,
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
                    takes_diabetes_meds,
                    diabetes_meds_str,
                    has_htn,
                    takes_htn_meds,
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

            # SEND SMS CONFIRMATION TO RESIDENT
            reg_sms_msg = f"Magandang araw {first_name}! Ikaw ay matagumpay na nairehistro sa PhilPEN Assessment Record ng Barangay {target_barangay}. CVD Risk Level: {risk_level}. Rekomendasyon: {recommended_action}."
            sms_sent, sms_log = send_sms_notification(contact_number, reg_sms_msg)

            if sms_sent:
                st.success(f"Record successfully saved to database! 📱 SMS Confirmation sent to {contact_number}.")
            else:
                st.success("Record successfully saved to database! (SMS failed to send or number invalid).")

# ---------------------------------------------------------
# MODULE 3: PHILPEN PROGRAM - PHILPEN DATABASE AND ANALYTICS
# ---------------------------------------------------------
elif main_nav == "   └ 📊 PhilPEN Database and Analytics":
    st.subheader(f"PhilPEN Database & Analytics — {portal_location_title}")

    tab_view, tab_analytics, tab_edit = st.tabs(
        ["📋 Master Records Data Table", "📊 Modern Analytics & Demographics", "✏️ Edit / Delete Resident Record"]
    )

    with tab_view:
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            export_filename = "PhilPEN_Municipal_Master_Palo.csv" if is_admin else f"PhilPEN_Records_{st.session_state['user_brgy']}.csv"
            st.download_button(
                label=f"Export CSV ({'All Barangays' if is_admin else st.session_state['user_brgy']})",
                data=csv,
                file_name=export_filename,
                mime="text/csv",
            )
        else:
            st.info("No records found in the database.")

    with tab_analytics:
        if df.empty:
            st.info("No assessment records found to analyze.")
        else:
            total_count = len(df)

            adults_df = df[(df["age"] >= 20) & (df["age"] <= 59)]
            elderly_df = df[df["age"] >= 60]
            adults_cnt = len(adults_df)
            elderly_cnt = len(elderly_df)

            diab_df = df[df["has_diabetes"] == "Meron"]
            htn_df = df[df["has_hypertension"] == "Meron"]
            diab_cnt = len(diab_df)
            htn_cnt = len(htn_df)
            high_risk_cnt = len(df[df["risk_level"].isin(["High", "Very High"])])

            st.markdown("#### 📈 **Epidemiological & Demographics Overview**")

            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Total Screened</div>
                        <div class="kpi-value">{total_count}</div>
                        <div class="kpi-subtext">100% Data</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            with k2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Adults (20-59 y/o)</div>
                        <div class="kpi-value" style="color: #38bdf8;">{adults_cnt}</div>
                        <div class="kpi-subtext">{round((adults_cnt/total_count)*100, 1) if total_count else 0}% Pop</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            with k3:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Elderly (60+ y/o)</div>
                        <div class="kpi-value" style="color: #fbbf24;">{elderly_cnt}</div>
                        <div class="kpi-subtext">{round((elderly_cnt/total_count)*100, 1) if total_count else 0}% Pop</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            with k4:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">High / Very High</div>
                        <div class="kpi-value" style="color: #f43f5e;">{high_risk_cnt}</div>
                        <div class="kpi-subtext">{round((high_risk_cnt/total_count)*100, 1) if total_count else 0}% CVD</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            with k5:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Diabetes Mellitus</div>
                        <div class="kpi-value" style="color: #a78bfa;">{diab_cnt}</div>
                        <div class="kpi-subtext">{round((diab_cnt/total_count)*100, 1) if total_count else 0}% Rate</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            with k6:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Hypertension</div>
                        <div class="kpi-value" style="color: #4ade80;">{htn_cnt}</div>
                        <div class="kpi-subtext">{round((htn_cnt/total_count)*100, 1) if total_count else 0}% Rate</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # ADMIN SPECIAL: ENHANCED BARANGAY SUMMARY MATRIX WITH EXACT TERMS
            if is_admin:
                st.markdown("### 🏛️ **Palo Municipal Screening Progress per Barangay**")
                
                brgy_rows = []
                for b in ONLY_BARANGAYS:
                    b_df = df[df["barangay"] == b]
                    b_tot = len(b_df)
                    if b_tot > 0:
                        b_htn = len(b_df[b_df["has_hypertension"] == "Meron"])
                        b_diab = len(b_df[b_df["has_diabetes"] == "Meron"])
                        b_cvd = len(b_df[b_df["risk_level"].isin(["High", "Very High"])])
                        b_bmi_prob = len(b_df[~b_df["bmi_class"].isin(["18.5 - 22.9 (NORMAL)", "N/A"])])
                        brgy_rows.append([b, b_tot, b_htn, b_diab, b_cvd, b_bmi_prob])
                    else:
                        brgy_rows.append([b, 0, 0, 0, 0, 0])

                brgy_rows.sort(key=lambda x: x[1], reverse=True)

                st.markdown(
                    render_modern_table_html(
                        "Barangay Health Screening Matrix",
                        ["Barangay Name", "Total Screened", "Hypertension", "Diabetes Mellitus", "High CVD Risk", "BMI Problem"],
                        brgy_rows
                    ),
                    unsafe_allow_html=True
                )
                st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 1: MONTHLY ENTRIES BREAKDOWN WITH ADULT & ELDERLY
            # ---------------------------------------------------------
            st.markdown("### 🗓️ **Monthly Assessment Entry Breakdown (January - December)**")
            
            st.markdown(
                f"""
                <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px 18px; margin-bottom: 18px; display: inline-block; text-align: left;">
                    <span style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Current Total Assessed (Palo, Leyte):</span>
                    <span style="color: #38bdf8; font-size: 1.3rem; font-weight: 700; margin-left: 10px;">{total_count}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            df["assessment_dt"] = pd.to_datetime(df["assessment_date"], errors="coerce")
            df["assessment_month"] = df["assessment_dt"].dt.strftime("%B")
            
            all_months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            monthly_rows = []
            for m in all_months:
                m_df = df[df["assessment_month"] == m]
                m_cnt = len(m_df[m_df["sex"] == "Male"])
                f_cnt = len(m_df[m_df["sex"] == "Female"])
                adult_cnt = len(m_df[(m_df["age"] >= 20) & (m_df["age"] <= 59)])
                elderly_cnt = len(m_df[m_df["age"] >= 60])
                tot_cnt = len(m_df)
                monthly_rows.append([m, m_cnt, f_cnt, adult_cnt, elderly_cnt, f"<strong>{tot_cnt}</strong>"])

            m_col1, m_col2 = st.columns([2.5, 1])
            with m_col1:
                st.markdown(
                    render_modern_table_html(
                        "Monthly Screening Distribution Summary (Sex & Age Disaggregated)",
                        ["Month", "Male", "Female", "Adults (20-59)", "Elderly (60+)", "Total Screened Entries"],
                        monthly_rows
                    ),
                    unsafe_allow_html=True
                )
            with m_col2:
                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; text-align: left;">
                        <h5 style="color: #818cf8; margin-top: 0; text-align: left;">📌 Month Tracking Notes</h5>
                        <p style="font-size: 0.85rem; color: #94a3b8; text-align: left;">
                            Ipinapakita sa talahanayan ang buwanang dami ng PhilPEN risk screening assessments na naisagawa (Kasarian: Lalaki at Babae; Edad: Adults 20-59 y/o at Elderly 60+ y/o) para sa buong taon.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 2: SEX-DISAGGREGATED ANALYTICS
            # ---------------------------------------------------------
            st.markdown("### ⚖️ **Sex Analytics Breakdown Matrix (Female vs Male)**")
            
            sex_col1, sex_col2 = st.columns(2)

            with sex_col1:
                htn_cross = pd.crosstab(df["has_hypertension"], df["sex"]).reset_index()
                htn_rows = []
                for _, r in htn_cross.iterrows():
                    m_val = r.get("Male", 0)
                    f_val = r.get("Female", 0)
                    htn_rows.append([str(r["has_hypertension"]), m_val, f_val, m_val + f_val])
                
                st.markdown(
                    render_modern_table_html(
                        "🫀 Hypertension Status by Sex",
                        ["Status", "Male", "Female", "Total"],
                        htn_rows
                    ),
                    unsafe_allow_html=True
                )

                bmi_cross = pd.crosstab(df["bmi_class"], df["sex"]).reset_index()
                bmi_rows = []
                for _, r in bmi_cross.iterrows():
                    m_val = r.get("Male", 0)
                    f_val = r.get("Female", 0)
                    bmi_rows.append([str(r["bmi_class"]), m_val, f_val, m_val + f_val])

                st.markdown(
                    render_modern_table_html(
                        "秤 BMI Classification by Sex",
                        ["BMI Classification", "Male", "Female", "Total"],
                        bmi_rows
                    ),
                    unsafe_allow_html=True
                )

            with sex_col2:
                diab_cross = pd.crosstab(df["has_diabetes"], df["sex"]).reset_index()
                diab_rows = []
                for _, r in diab_cross.iterrows():
                    m_val = r.get("Male", 0)
                    f_val = r.get("Female", 0)
                    diab_rows.append([str(r["has_diabetes"]), m_val, f_val, m_val + f_val])

                st.markdown(
                    render_modern_table_html(
                        "🩸 Diabetes Mellitus Status by Sex",
                        ["Status", "Male", "Female", "Total"],
                        diab_rows
                    ),
                    unsafe_allow_html=True
                )

                risk_cross = pd.crosstab(df["risk_level"], df["sex"]).reset_index()
                risk_rows = []
                for _, r in risk_cross.iterrows():
                    m_val = r.get("Male", 0)
                    f_val = r.get("Female", 0)
                    risk_rows.append([str(r["risk_level"]), m_val, f_val, m_val + f_val])

                st.markdown(
                    render_modern_table_html(
                        "🎯 CVD Risk Stratification by Sex",
                        ["CVD Risk Level", "Male", "Female", "Total"],
                        risk_rows
                    ),
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 3: TABULATED CATEGORICAL ANALYTICS
            # ---------------------------------------------------------
            st.markdown("### 📊 **Categorical Summary Tables**")

            summary_c1, summary_c2 = st.columns(2)

            with summary_c1:
                cvd_summary = df["risk_level"].value_counts().reset_index()
                cvd_summary.columns = ["Risk Level", "Count"]
                cvd_rows = [
                    [row["Risk Level"], row["Count"], f"{round((row['Count']/total_count)*100, 1)}%"]
                    for _, row in cvd_summary.iterrows()
                ]
                st.markdown(
                    render_modern_table_html(
                        "🎯 CVD Risk Stratification Distribution",
                        ["Risk Level", "Total Population", "Percentage"],
                        cvd_rows
                    ),
                    unsafe_allow_html=True
                )

                bins = [0, 19, 59, 120]
                labels = ["Youth (<20 y/o)", "Adults (20-59 y/o)", "Elderly (60+ y/o)"]
                df["age_demo"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)
                age_demo_summary = df["age_demo"].value_counts().reset_index()
                age_demo_summary.columns = ["Demographic Category", "Count"]
                age_demo_rows = [
                    [row["Demographic Category"], row["Count"], f"{round((row['Count']/total_count)*100, 1)}%"]
                    for _, row in age_demo_summary.iterrows()
                ]
                st.markdown(
                    render_modern_table_html(
                        "👥 Demographics Age Category Summary",
                        ["Age Group", "Total Screened", "Percentage"],
                        age_demo_rows
                    ),
                    unsafe_allow_html=True
                )

            with summary_c2:
                bmi_summary = df["bmi_class"].value_counts().reset_index()
                bmi_summary.columns = ["BMI Category", "Count"]
                bmi_sum_rows = [
                    [row["BMI Category"], row["Count"], f"{round((row['Count']/total_count)*100, 1)}%"]
                    for _, row in bmi_summary.iterrows()
                ]
                st.markdown(
                    render_modern_table_html(
                        "⚖️ Body Mass Index (BMI) Distribution Table",
                        ["BMI Category", "Total Count", "Percentage"],
                        bmi_sum_rows
                    ),
                    unsafe_allow_html=True
                )

                lifestyle_rows = [
                    ["Smoker (Naninigarilyo)", len(df[df["is_smoker"] == "Oo"]), f"{round((len(df[df['is_smoker'] == 'Oo'])/total_count)*100, 1)}%"],
                    ["Binge Drinker", len(df[df["is_binge_drinker"] == "Oo"]), f"{round((len(df[df['is_binge_drinker'] == 'Oo'])/total_count)*100, 1)}%"],
                    ["Inadequate Exercise (<150 min/wk)", len(df[df["is_exercising"] == "Hindi"]), f"{round((len(df[df['is_exercising'] == 'Hindi'])/total_count)*100, 1)}%"],
                    ["Unhealthy Diet (<5 servings/day)", len(df[df["eats_healthy"] == "Hindi"]), f"{round((len(df[df['eats_healthy'] == 'Hindi'])/total_count)*100, 1)}%"],
                ]
                st.markdown(
                    render_modern_table_html(
                        "🚬 Lifestyle Risk Factors Summary Table",
                        ["Lifestyle Risk Factor", "Affected Residents", "Prevalence Rate"],
                        lifestyle_rows
                    ),
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 4: CHRONIC DISEASE PATIENT ROSTERS WITH DOWNLOAD
            # ---------------------------------------------------------
            st.markdown("### 🩺 **Diabetes Mellitus and Hypertension Resident Rosters**")
            roster_col1, roster_col2 = st.columns(2)

            with roster_col1:
                st.markdown("#### 🩸 **List of Residents with Diabetes Mellitus**")
                if not diab_df.empty:
                    # FULL INFORMATION DOWNLOAD FOR DIABETES
                    diab_full_csv = diab_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Diabetes Roster (All Patient Information CSV)",
                        data=diab_full_csv,
                        file_name=f"Diabetes_Mellitus_Roster_Full_{st.session_state['user_brgy']}.csv",
                        mime="text/csv",
                        key="btn_dl_diab_full",
                    )
                    diab_cols = ["id", "barangay", "last_name", "first_name", "age", "sex", "zone", "contact_number", "takes_diabetes_meds", "diabetes_meds", "bp_avg", "action_taken", "assessor_name"] if is_admin else ["id", "last_name", "first_name", "age", "sex", "zone", "contact_number", "takes_diabetes_meds", "diabetes_meds", "bp_avg", "action_taken", "assessor_name"]
                    st.dataframe(diab_df[diab_cols], use_container_width=True)
                else:
                    st.success("No Residents with Diabetes Mellitus recorded.")

            with roster_col2:
                st.markdown("#### 🫀 **List of Residents with Hypertension**")
                if not htn_df.empty:
                    # FULL INFORMATION DOWNLOAD FOR HYPERTENSION
                    htn_full_csv = htn_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Hypertension Roster (All Patient Information CSV)",
                        data=htn_full_csv,
                        file_name=f"Hypertension_Roster_Full_{st.session_state['user_brgy']}.csv",
                        mime="text/csv",
                        key="btn_dl_htn_full",
                    )
                    htn_cols = ["id", "barangay", "last_name", "first_name", "age", "sex", "zone", "contact_number", "takes_htn_meds", "hypertension_meds", "bp_avg", "action_taken", "assessor_name"] if is_admin else ["id", "last_name", "first_name", "age", "sex", "zone", "contact_number", "takes_htn_meds", "hypertension_meds", "bp_avg", "action_taken", "assessor_name"]
                    st.dataframe(htn_df[htn_cols], use_container_width=True)
                else:
                    st.success("No Residents with Hypertension recorded.")

            st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 5: BHW / ASSESSOR SCREENING TALLY SHEET
            # ---------------------------------------------------------
            st.markdown("### 👩‍⚕️ **BHW / Assessor Assessment Tally Sheet**")
            
            if "assessor_name" in df.columns:
                bhw_counts = df["assessor_name"].fillna("Unassigned / Not Specified").value_counts().reset_index()
                bhw_counts.columns = ["Name of BHW / Assessor", "Number of Residents Assessed"]
                
                bhw_rows = [
                    [
                        row["Name of BHW / Assessor"] if str(row["Name of BHW / Assessor"]).strip() != "" else "Unassigned / Not Specified",
                        row["Number of Residents Assessed"]
                    ]
                    for _, row in bhw_counts.iterrows()
                ]

                bhw_col1, bhw_col2 = st.columns([2, 1])
                with bhw_col1:
                    st.markdown(
                        render_modern_table_html(
                            "Tally of Residents Assessed per BHW / Assessor",
                            ["Name of BHW / Assessor", "Number of Residents Assessed"],
                            bhw_rows
                        ),
                        unsafe_allow_html=True
                    )
                with bhw_col2:
                    st.markdown(
                        """
                        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; text-align: left;">
                            <h5 style="color: #818cf8; margin-top: 0; text-align: left;">📌 BHW Tally Summary</h5>
                            <p style="font-size: 0.85rem; color: #94a3b8; text-align: left;">
                                Ipinapakita sa talahanayang ito ang kabuuang bilang ng mga residenteng na-assess ng bawat Barangay Health Worker (BHW) o Assessor.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with tab_edit:
        if df.empty:
            st.info("No records available to edit or delete.")
        else:
            st.markdown("#### 🔍 **Search & Select Resident Record**")
            search_term = st.text_input("🔎 Search Resident by Full Name, Last Name, or First Name:", key="edit_search_term")
            
            if search_term.strip():
                matching_mask = df.apply(
                    lambda r: search_term.lower() in f"{r['first_name']} {r['middle_name'] or ''} {r['last_name']}".lower() or 
                              search_term.lower() in f"{r['last_name']}, {r['first_name']}".lower(),
                    axis=1
                )
                search_df = df[matching_mask]
            else:
                search_df = df

            if search_df.empty:
                st.warning("No matching resident records found for the given search term.")
            else:
                resident_options = {
                    f"ID {row['id']}: [{row['barangay']}] {row['last_name']}, {row['first_name']} {row['middle_name'] or ''} (DOB: {row['birthday']})": row["id"]
                    for _, row in search_df.iterrows()
                }
                selected_label = st.selectbox("Select Resident Record to Edit or Delete:", list(resident_options.keys()))
                record_id = resident_options[selected_label]
                rec = df[df["id"] == record_id].iloc[0]

                # ---------------------------------------------------------
                # DELETE RECORD SECTION
                # ---------------------------------------------------------
                with st.expander("🗑️ **Delete Resident Record**", expanded=False):
                    st.markdown(
                        f"""
                        <div class="flag-red-card" style="margin-bottom: 10px;">
                            <h4>⚠️ CONFIRM RECORD DELETION</h4>
                            <p>
                                Sigurado ka ba na gusto mong burahin ang record ni <strong>{rec['first_name'].upper()} {rec['last_name'].upper()}</strong> (ID #{record_id}) mula sa Barangay <strong>{rec['barangay']}</strong>?<br>
                                🚨 <em>Ang aksyong ito ay hindi na mababawi pagkatapos kumpirmahin.</em>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    if st.button("🔴 Permanently Delete Record", key=f"btn_delete_rec_{record_id}"):
                        conn = sqlite3.connect("philpen_palo.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM assessments WHERE id = ?", (record_id,))
                        conn.commit()
                        conn.close()

                        st.success(f"Record ID #{record_id} ({rec['first_name']} {rec['last_name']}) has been successfully deleted from the database.")
                        st.rerun()

                st.markdown("---")
                st.markdown(f"#### ✏️ **Edit Resident Record — ID #{record_id}**")

                with st.form("edit_full_resident_form"):
                    st.markdown("**1. General & Assessor Information**")
                    
                    ec0_a, ec0_b = st.columns(2)
                    with ec0_a:
                        e_assessor_name = st.text_input("Pangalan ng BHW / Assessor", value=str(rec.get("assessor_name", "")))
                    with ec0_b:
                        try:
                            curr_ass_date = datetime.datetime.strptime(str(rec["assessment_date"]), "%Y-%m-%d").date()
                        except ValueError:
                            curr_ass_date = datetime.date.today()
                        e_assessment_date = st.date_input("Assessment Date", value=curr_ass_date)

                    # ONE LINE EDIT: Apilido, Pangalan, Gitnang Pangalan
                    e_col_lname, e_col_fname, e_col_mname = st.columns(3)
                    with e_col_lname:
                        e_last_name = st.text_input("Apilido (Last Name)", value=str(rec["last_name"]))
                    with e_col_fname:
                        e_first_name = st.text_input("Pangalan (Given Name)", value=str(rec["first_name"]))
                    with e_col_mname:
                        e_middle_name = st.text_input("Gitnang Pangalan (Middle Name)", value=str(rec["middle_name"] or ""))

                    # ONE LINE EDIT: Zone/Purok, Barangay, Contact Number
                    e_col_zone, e_col_brgy, e_col_contact = st.columns(3)
                    with e_col_zone:
                        e_zone = st.text_input("Zone / Purok", value=str(rec["zone"]))
                    with e_col_brgy:
                        if is_admin:
                            curr_brgy_val = str(rec["barangay"])
                            e_brgy_idx = ONLY_BARANGAYS.index(curr_brgy_val) if curr_brgy_val in ONLY_BARANGAYS else 0
                            e_barangay = st.selectbox("Barangay", ONLY_BARANGAYS, index=e_brgy_idx)
                        else:
                            e_barangay = st.text_input("Barangay", value=str(rec["barangay"]), disabled=True)
                    with e_col_contact:
                        e_contact_number = st.text_input("Contact Number", value=str(rec.get("contact_number", "")))

                    ec_dob, ec_sex = st.columns(2)
                    with ec_dob:
                        try:
                            curr_dob = datetime.datetime.strptime(str(rec["birthday"]), "%Y-%m-%d").date()
                        except ValueError:
                            curr_dob = datetime.date(1990, 1, 1)
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

                    st.markdown("**3. Medical History & Specific Medications**")
                    ehtn_col, ediab_col = st.columns(2)

                    with ehtn_col:
                        htn_options = ["Wala", "Meron", "Diri ak maaram"]
                        htn_idx = htn_options.index(rec["has_hypertension"]) if rec["has_hypertension"] in htn_options else 0
                        e_has_htn = st.selectbox("May Hypertension?", htn_options, index=htn_idx)

                        curr_takes_htn = str(rec.get("takes_htn_meds", "Wala"))
                        e_takes_htn_meds = st.radio(
                            "May iniinom ka bang gamot para sa Hypertension?",
                            ["Wala", "Meron"],
                            index=1 if curr_takes_htn == "Meron" else 0
                        )

                        curr_htn_meds = [m.strip() for m in str(rec["hypertension_meds"]).split(",") if m.strip()]
                        e_htn_meds = st.multiselect(
                            "Hypertension Medications", 
                            options=HYPERTENSION_MEDICATIONS, 
                            default=[m for m in curr_htn_meds if m in HYPERTENSION_MEDICATIONS]
                        )

                    with ediab_col:
                        diab_options = ["Wala", "Meron", "Diri ak maaram"]
                        diab_idx = diab_options.index(rec["has_diabetes"]) if rec["has_diabetes"] in diab_options else 0
                        e_has_diabetes = st.selectbox("May Diabetes Mellitus?", diab_options, index=diab_idx)

                        curr_takes_diab = str(rec.get("takes_diabetes_meds", "Wala"))
                        e_takes_diabetes_meds = st.radio(
                            "May gamot ka ba na iniinom para sa Diabetes Mellitus?",
                            ["Wala", "Meron"],
                            index=1 if curr_takes_diab == "Meron" else 0
                        )

                        curr_diab_meds = [m.strip() for m in str(rec["diabetes_meds"]).split(",") if m.strip()]
                        e_diab_meds = st.multiselect(
                            "Diabetes Mellitus Medications", 
                            options=DIABETES_MEDICATIONS, 
                            default=[m for m in curr_diab_meds if m in DIABETES_MEDICATIONS]
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
                        e_exercise = st.radio("Exercises 150m/wk", ny_opts, index=0 if rec["eats_healthy"] == "Oo" else 1)
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

                        new_risk_level, _, _, _, e_rec_action = calculate_cvd_risk(e_age, e_sex, e_smoker, e_systolic, new_bmi, e_has_diabetes)
                        e_diab_meds_str = ", ".join(e_diab_meds) if (e_takes_diabetes_meds == "Meron" and e_diab_meds) else "Wala"
                        e_htn_meds_str = ", ".join(e_htn_meds) if (e_takes_htn_meds == "Meron" and e_htn_meds) else "Wala"

                        conn = sqlite3.connect("philpen_palo.db")
                        c = conn.cursor()
                        c.execute(
                            """
                            UPDATE assessments SET
                                assessment_date=?, assessor_name=?, last_name=?, first_name=?, middle_name=?, zone=?, barangay=?, contact_number=?,
                                birthday=?, age=?, sex=?, weight_kg=?, height_cm=?, bmi=?, bmi_class=?,
                                waist_cm=?, waist_risk=?, has_diabetes=?, takes_diabetes_meds=?, diabetes_meds=?, 
                                has_hypertension=?, takes_htn_meds=?, hypertension_meds=?, high_cholesterol=?, 
                                history_cvd_stroke=?, history_heart_attack=?, history_kidney=?, family_history=?, 
                                bp_1=?, bp_2=?, bp_3=?, bp_avg=?, is_smoker=?, is_binge_drinker=?, is_exercising=?, 
                                eats_healthy=?, risk_level=?, action_taken=?
                            WHERE id=?
                        """,
                            (
                                str(e_assessment_date),
                                e_assessor_name,
                                e_last_name,
                                e_first_name,
                                e_middle_name,
                                e_zone,
                                e_barangay,
                                e_contact_number,
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
                                e_takes_diabetes_meds,
                                e_diab_meds_str,
                                e_has_htn,
                                e_takes_htn_meds,
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

                        # SEND UPDATE SMS NOTIFICATION TO RESIDENT
                        update_sms_msg = f"Magandang araw {e_first_name}! Ang iyong PhilPEN Assessment Record ay na-update na. Bagong CVD Risk Level: {new_risk_level}. Action Taken: {e_action}."
                        sms_sent, _ = send_sms_notification(e_contact_number, update_sms_msg)

                        if sms_sent:
                            st.success(f"All record details updated successfully! 📱 Update SMS sent to {e_contact_number}.")
                        else:
                            st.success("All record details updated successfully! Analytics dashboard updated.")
                        st.rerun()

# ---------------------------------------------------------
# OTHER HEALTH PROGRAM MODULES
# ---------------------------------------------------------
elif main_nav == "Mental Health Program":
    st.subheader(f"Mental Health Program — {portal_location_title}")
    st.info("The **Mental Health Program** module is scheduled for data integration.")

else:
    st.subheader(f"{main_nav} Module — {portal_location_title}")
    st.info(f"The **{main_nav}** module is scheduled for data integration.")
