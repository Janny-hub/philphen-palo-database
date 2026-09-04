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
# CONSTANTS & LISTS
# ---------------------------------------------------------
BARANGAYS = [
    "Anahaway",
    "Arado",
    "Baras",
    "Barayong",
    "Cabarasan Daku",
    "Cabarasan Guti",
    "Campetic",
    "Candahug",
    "Cangumbang",
    "Canhidoc",
    "Capirawan",
    "Castilla",
    "Cogon",
    "San Joaquin",
    "Gacao",
    "Guindapunan",
    "Libertad",
    "Naga-naga",
    "Pawing",
    "Buri (Poblacion barangay)",
    "Cavite East (Pob. barangay)",
    "Cavite West (Poblacion)",
    "Luntad (Poblacion)",
    "Santa Cruz (Poblacion)",
    "Salvacion",
    "San Agustin",
    "San Antonio",
    "San Isidro",
    "San Jose",
    "St. Michael (Poblacion)",
    "Tacuranga",
    "Teraza",
    "San Fernando",
]

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
    # Simplified WHO Non-Laboratory Risk Matrix
    if diabetes == "Meron" or sbp >= 160 or bmi >= 25.0:
        if age >= 60 or sbp >= 160:
            return "High", "20% to <30%", "Red"
        return "Medium", "10% to <20%", "Orange"
    elif smoker == "Oo" or sbp >= 140:
        return "Mild", "5% to <10%", "Yellow"
    return "Low", "<5%", "Green"


# ---------------------------------------------------------
# AUTHENTICATION & BARANGAY LOCK
# ---------------------------------------------------------
st.set_page_config(
    page_title="PhilPEN Risk Assessment - Palo Leyte", layout="wide"
)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_brgy"] = ""
    st.session_state["bhw_name"] = ""

if not st.session_state["authenticated"]:
    st.title("PhilPEN Risk Assessment Portal")
    st.subheader("Palo, Leyte - Health Worker Login")

    with st.form("login_form"):
        brgy = st.selectbox("Select Your Barangay", BARANGAYS)
        bhw = st.text_input("BHW Full Name")
        pin = st.text_input("Barangay Security Code / PIN", type="password")
        submit = st.form_submit_button("Access Portal")

        if submit:
            if pin == "1234":  # Replace with actual PIN verification
                st.session_state["authenticated"] = True
                st.session_state["user_brgy"] = brgy
                st.session_state["bhw_name"] = bhw
                st.rerun()
            else:
                st.error("Invalid Security Code")
    st.stop()

# ---------------------------------------------------------
# MAIN APP INTERFACE
# ---------------------------------------------------------
st.sidebar.title(f"📍 {st.session_state['user_brgy']}")
st.sidebar.write(f"**BHW:** {st.session_state['bhw_name']}")
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

menu = st.sidebar.radio("Navigation", ["New Assessment", "Barangay Database"])

if menu == "New Assessment":
    st.title("PhilPEN Health Risk Assessment Form")

    with st.form("assessment_form"):
        st.subheader("1. General Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            assessment_date = st.date_input(
                "Date of Assessment", datetime.date.today()
            )
            last_name = st.text_input("Apilido (Last Name)*")
        with col2:
            first_name = st.text_input("Pangalan (Given Name)*")
            middle_name = st.text_input("Gitnang Pangalan (Middle Name)")
        with col3:
            zone = st.text_input("Zone / Purok*")
            barangay = st.text_input(
                "Barangay", value=st.session_state["user_brgy"], disabled=True
            )

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

        st.subheader("2. Body Measurements & Auto-Calculations")
        col_w, col_h = st.columns(2)
        with col_w:
            weight = st.number_input(
                "Timbang / Weight (kg)*", min_value=1.0, max_value=300.0, step=0.5
            )
        with col_h:
            height = st.number_input(
                "Taas / Height (cm)*", min_value=30.0, max_value=250.0, step=0.5
            )

        bmi = calculate_bmi(weight, height)
        bmi_cat = classify_bmi(bmi)
        st.success(
            f"**Calculated BMI:** {bmi} | **Classification:** {bmi_cat}"
        )

        waist = st.number_input(
            "Waist Circumference (cm)*", min_value=20.0, max_value=200.0, step=0.5
        )
        waist_risk = classify_waist(sex, waist)
        st.info(f"**Waist Risk Status:** {waist_risk}")

        st.subheader("3. Medical History")
        has_diabetes = st.selectbox(
            "May ada ka ba Diabetes?*", ["Wala", "Meron", "Diri ak maaram"]
        )
        diabetes_meds = st.text_input("Ano ang iniinom mong gamot para sa Diabetes?")

        has_htn = st.selectbox(
            "May ada ka ba High blood / Hypertension?*",
            ["Wala", "Meron", "Diri ak maaram"],
        )
        htn_meds = st.text_input("Ano ang iniinom mong gamot para sa Hypertension?")

        cholesterol = st.selectbox(
            "Hitaas ba an iyo cholesterol?*", ["Hindi", "Oo", "Diri ak maaram"]
        )

        st.write("**Na-diagnose na po ba kamo hinin mga sakit?**")
        cvd_stroke = st.checkbox("History of CVD (Stroke)")
        heart_attack = st.checkbox("History of Heart attack (Naatake sa puso)")
        kidney_prob = st.checkbox("Chronic Kidney Problem (Dialysis patient)")

        fam_history = st.selectbox(
            "Family History: May ada ba inatake ha puso o na-stroke?",
            ["Wala", "Meron"],
        )

        st.subheader("4. Blood Pressure Screening")
        bp1 = st.text_input("Unang Blood Pressure (e.g., 120/80)*")

        systolic = 120
        if bp1 and "/" in bp1:
            try:
                systolic = int(bp1.split("/")[0])
            except ValueError:
                pass

        bp2 = ""
        bp3 = ""
        bp_avg = bp1
        if systolic >= 140:
            st.warning("BP is ≥ 140/90. Please rest for 15 minutes and retake.")
            bp2 = st.text_input("Pangalawang Blood Pressure (optional)")
            bp3 = st.text_input("Pangatlong Blood Pressure (optional)")
            if bp2 and bp3 and "/" in bp2 and "/" in bp3:
                try:
                    s2, d2 = map(int, bp2.split("/"))
                    s3, d3 = map(int, bp3.split("/"))
                    bp_avg = f"{(s2+s3)//2}/{(d2+d3)//2}"
                except ValueError:
                    pass

        st.subheader("5. Lifestyle & Risk Stratification")
        smoker = st.radio("Ikaw ba ay naninigarilyo?*", ["Hindi", "Oo"])
        drinker = st.radio("Ikaw ba ay binge drinker?*", ["Hindi", "Oo"])
        exercise = st.radio(
            "Nakakapag-ehersisyo ka ba 150 mins/week?*", ["Oo", "Hindi"]
        )
        healthy_diet = st.radio(
            "Nakakakain ng 5 platitong gulay/prutas araw-araw?*", ["Oo", "Hindi"]
        )

        risk_level, risk_pct, risk_color = calculate_cvd_risk(
            age, sex, smoker, systolic, bmi, has_diabetes
        )
        st.markdown(
            f"### **WHO/ISH Risk Assessment: {risk_level} Risk ({risk_pct})**"
        )

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
                    is_exercising, eats_healthy, risk_level, action_taken, bhw_name
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                    st.session_state["bhw_name"],
                ),
            )
            conn.commit()
            conn.close()
            st.success("Record saved successfully to database!")

elif menu == "Barangay Database":
    st.title(f"Patient Database - Barangay {st.session_state['user_brgy']}")
    conn = sqlite3.connect("philpen_palo.db")
    df = pd.read_sql_query(
        "SELECT * FROM assessments WHERE barangay = ?",
        conn,
        params=(st.session_state["user_brgy"],),
    )
    conn.close()

    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export Barangay Records (CSV)",
            data=csv,
            file_name=f"PhilPEN_{st.session_state['user_brgy']}.csv",
            mime="text/csv",
        )
    else:
        st.info("No assessment records found for this Barangay yet.")
