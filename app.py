import streamlit as st
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.markdown("""
    <style>
    /* Ocultar menú y header */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Eliminar padding superior del body */
    .block-container {
        padding-top: 0rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide")

# --- DATA DICTIONARIES ---
xerop = {"Never": 0, "Sometimes": 1, "Always": 2}
medop = {"No": 0, "Yes": 1}
diabop = {"No": 0, "Yes": 1}

halop = {"0": 1, "1": 1, "2": 2, "3": 2, "4": 3, "5": 3}
candop = {"No": 0, "Yes": 2}
lendop = {"No": 0, "Yes": 1}
perdop = {"None": 0, "Moderate": 1, "Severe": 2}

ckdop = {"0": 0, "1": 0, "2": 0, "3": 1, "4": 2, "5": 2, "Dialysis": 3}

h = 552
hf = 775


# --- REPORT CONTENT DATA ---
indicator_explanations = {
    "Dry mouth / Xerostomia": (
        "Dry mouth means your mouth often feels dry, sticky, or uncomfortable. "
        "It may make it harder to speak, chew, swallow, or taste food."
    ),
    "Medications causing dry mouth": (
        "Some medicines, such as diuretics or antihypertensive drugs, may reduce saliva "
        "and make your mouth feel dry."
    ),
    "Diabetes": (
        "Diabetes may increase the risk of gum disease, oral infection, delayed healing, "
        "and dry mouth."
    ),
    "Bad breath / Halitosis": (
        "Bad breath means an unpleasant smell from the mouth. It may be related to dry mouth, "
        "tongue coating, gum disease, tooth decay, or oral infection."
    ),
    "Oral candidiasis": (
        "Oral candidiasis is a fungal infection in the mouth. It may appear as white patches, "
        "redness, soreness, burning, or a cotton-like feeling."
    ),
    "Tongue fissuring / Scrotal tongue": (
        "A fissured tongue has deep lines, cracks, or grooves on the surface. Food or bacteria "
        "may stay in the grooves and cause discomfort or bad breath."
    ),
    "Periodontal disease": (
        "Periodontal disease, also called gum disease, affects the gums and tissues supporting "
        "the teeth. Signs may include bleeding gums, swollen gums, bad breath, loose teeth, "
        "or pain when chewing."
    ),
    "CKD stage": (
        "CKD stage describes the severity of chronic kidney disease. A higher stage usually means "
        "more serious kidney disease and may be associated with more oral health concerns."
    ),
}

specific_recommendations = {
    "Dry mouth / Xerostomia": [
        "Sip water frequently if this is allowed by your kidney doctor.",
        "Use sugar-free chewing gum or sugar-free lozenges to help stimulate saliva.",
        "Ask your dentist or doctor about saliva substitutes or dry mouth products.",
    ],
    "Medications causing dry mouth": [
        "Do not stop any medication by yourself.",
        "Ask your doctor whether your medication may be contributing to dry mouth.",
        "Tell your dentist about all medications you are currently taking.",
    ],
    "Diabetes": [
        "Maintain good blood sugar control as advised by your healthcare provider.",
        "Check your gums regularly for bleeding, swelling, or signs of infection.",
        "Schedule regular dental visits because diabetes may increase the risk of gum disease.",
    ],
    "Bad breath / Halitosis": [
        "Brush your teeth and tongue gently every day.",
        "Clean between your teeth with floss or interdental brushes.",
        "If bad breath continues, visit a dentist to check for gum disease, tooth decay, or infection.",
    ],
    "Oral candidiasis": [
        "Visit a dentist or doctor if you notice white patches, soreness, burning, or a cotton-like feeling.",
        "Avoid self-medicating without professional advice.",
        "Keep dentures, retainers, or oral appliances clean if you use them.",
    ],
    "Tongue fissuring / Scrotal tongue": [
        "Clean your tongue gently to remove trapped food or debris.",
        "Avoid spicy, acidic, or irritating foods if your tongue feels sore.",
        "Ask a dentist to check your tongue if there is pain, swelling, or persistent discomfort.",
    ],
    "Periodontal disease": [
        "Visit a dentist or periodontist for a gum evaluation.",
        "Professional cleaning may be needed to remove plaque and calculus.",
        "Seek dental care if your gums bleed, swell, hurt, or if your teeth feel loose.",
    ],
    "CKD stage": [
        "Keep both your kidney doctor and dentist informed about your health condition.",
        "Ask your healthcare team before major dental procedures if you have advanced CKD or are on dialysis.",
        "Maintain regular oral care because oral infection may affect general health.",
    ],
}

general_recommendations = [
    "Brush your teeth gently at least twice a day using fluoride toothpaste.",
    "Clean between your teeth daily with dental floss or interdental brushes.",
    "Drink enough water if allowed by your kidney doctor, especially if your mouth feels dry.",
    "Avoid smoking and limit alcohol, as they may worsen dry mouth, gum problems, and bad breath.",
    "Visit a dentist regularly for oral examination and professional cleaning.",
    "Tell your dentist if you have chronic kidney disease, diabetes, or take long-term medications.",
    "Do not ignore bleeding gums, loose teeth, white patches, mouth pain, or persistent bad breath.",
    "If you are on dialysis or have advanced CKD, discuss dental treatment timing with your healthcare team.",
]


# Initialize calculation state if it doesn't exist
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
    st.session_state.total_points = 0 


# --- PDF REPORT FUNCTIONS ---
def get_risk_level(points):
    if points <= 3:
        return "Low Risk"
    elif 4 <= points <= 6:
        return "Moderate Risk"
    else:
        return "High Risk"


def get_risk_message(points):
    if points <= 3:
        return (
            "Your current score suggests a low level of oral health-related risk. "
            "However, maintaining good daily oral hygiene and regular dental check-ups is still important."
        )
    elif 4 <= points <= 6:
        return (
            "Your current score suggests a moderate level of oral health-related risk. "
            "Some oral health signs may need more attention. You are advised to improve daily oral care "
            "and consider visiting a dentist for further evaluation."
        )
    else:
        return (
            "Your current score suggests a high level of oral health-related risk. "
            "Several oral health or medical factors may require professional attention. "
            "You are strongly advised to consult a dentist and discuss your oral health with your healthcare team."
        )


def build_patient_report_pdf(patient_data, total_points):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.grey
    )

    elements = []

    elements.append(Paragraph("Oral Health & CKD Risk Calculator Report", title_style))
    elements.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 12))

    risk_level = get_risk_level(total_points)
    risk_message = get_risk_message(total_points)

    summary_data = [
        ["Total Score", str(total_points)],
        ["Risk Category", risk_level]
    ]

    summary_table = Table(summary_data, colWidths=[2.2 * inch, 3.8 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(Paragraph("Risk Assessment Summary", heading_style))
    elements.append(summary_table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(risk_message, normal_style))
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Patient Responses and Scores", heading_style))

    table_data = [["Indicator", "Patient Response", "Score"]]

    for item in patient_data:
        table_data.append([
            Paragraph(item["indicator"], normal_style),
            Paragraph(str(item["response"]), normal_style),
            Paragraph(str(item["score"]), normal_style)
        ])

    indicator_table = Table(table_data, colWidths=[2.7 * inch, 2.4 * inch, 0.8 * inch])
    indicator_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(indicator_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("What Each Indicator Means", heading_style))

    for item in patient_data:
        indicator = item["indicator"]
        explanation = indicator_explanations.get(indicator, "")
        elements.append(Paragraph(f"<b>{indicator}</b>", normal_style))
        elements.append(Paragraph(explanation, normal_style))
        elements.append(Spacer(1, 6))

    elements.append(Paragraph("Personalized Suggestions", heading_style))

    added_any_specific = False

    for item in patient_data:
        indicator = item["indicator"]
        score = item["score"]

        if score > 0:
            suggestions = specific_recommendations.get(indicator, [])

            if suggestions:
                added_any_specific = True
                elements.append(Paragraph(f"<b>{indicator}</b>", normal_style))

                for suggestion in suggestions:
                    elements.append(Paragraph(f"- {suggestion}", normal_style))

                elements.append(Spacer(1, 6))

    if not added_any_specific:
        elements.append(Paragraph(
            "No major risk-related answers were selected. Please continue maintaining good daily oral hygiene.",
            normal_style
        ))

    elements.append(Paragraph("General Oral Health Advice", heading_style))

    for rec in general_recommendations:
        elements.append(Paragraph(f"- {rec}", normal_style))

    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Important Reminder", heading_style))
    elements.append(Paragraph(
        "This report is for educational and self-awareness purposes only. "
        "It does not provide a medical diagnosis and should not replace professional advice from a dentist, "
        "physician, nephrologist, or other healthcare provider.",
        small_style
    ))

    doc.build(elements)

    buffer.seek(0)
    return buffer


# Create main columns (3:1 ratio)
col_main_left, col_final_right = st.columns([3, 1])

# --- LEFT COLUMN LOGIC ---
with col_main_left:
    # Row 1: Title (Spans across 3 sub-columns)
    st.title('Oral Health Index & CKD Risk Calculator')
    st.text('This calculator aims to estimate the percentage risk by which a patient’s oral health status may contribute to the development or progression of chronic kidney disease (CKD).')


    # -------------------------
    # Accessibility
    # -------------------------
    font_option = st.selectbox(
        "Customizable Font Size",
        ["Small", "Medium", "Large"],
        index=1
    )

    font_sizes = {
        "Small": "13px",
        "Medium": "15px",
        "Large": "17px"
    }

    selected_size = font_sizes[font_option]

    st.markdown(f"""
    <style>

    /* Mantener SIEMPRE el tamaño del título principal */
    h1 {{
        font-size: 2.5rem !important;
    }}

    /* Labels */
    label {{
        font-size: {selected_size} !important;
    }}

    /* Selectboxes */
    [data-baseweb="select"] {{
        font-size: {selected_size} !important;
    }}

    /* Botones */
    button {{
        font-size: {selected_size} !important;
    }}

    /* Texto normal */
    [data-testid="stMarkdownContainer"] p {{
        font-size: {selected_size} !important;
    }}

    /* st.text() */
    [data-testid="stText"] {{
        font-size: {selected_size} !important;
    }}

    </style>
    """, unsafe_allow_html=True)

    # Row 2: Split into 3 sub-columns
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    
    with sub_col1:
        with st.container(height=h, border=True):
            st.header("About you")

            # ------------------------
            # Xerostomia
            # ------------------------
            @st.dialog("What is dry mouth?")
            def show_xerostomia_popup():

                st.write("""
                Dry mouth (xerostomia) is the feeling that your mouth is
                unusually dry, sticky, or lacks saliva.

                It may make speaking, eating, swallowing, or wearing
                dentures more difficult.

                Compare your symptoms with the reference image below.
                """)

                st.image(
                    "images/1.jpg",
                    use_container_width=True
                )

            col1, col2 = st.columns([8,1])

            with col1:
                xer = st.selectbox(
                    "Does your mouth often feel dry or sticky?",
                    list(xerop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("ℹ️", key="xer_info"):
                    show_xerostomia_popup()


            # ------------------------
            # Medications
            # ------------------------
            @st.dialog("Why are we asking this?")
            def show_med_popup():

                st.write("""
                Some medications may reduce saliva production and
                contribute to dry mouth.

                Common examples include some blood pressure medications,
                diuretics, antidepressants, and antihistamines.
                """)

            col1, col2 = st.columns([8,1])

            with col1:
                med = st.selectbox(
                    "Do you take any medication that causes dry mouth?",
                    list(medop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("ℹ️", key="med_info"):
                    show_med_popup()


            # ------------------------
            # Diabetes
            # ------------------------
            @st.dialog("Why is diabetes important?")
            def show_diabetes_popup():

                st.write("""
                Diabetes can affect oral health by increasing the risk
                of gum disease, oral infections, delayed healing, and
                dry mouth.

                Good oral health is especially important for people
                living with diabetes.
                """)

            col1, col2 = st.columns([8,1])

            with col1:
                diab = st.selectbox(
                    "Have you been diagnosed with diabetes?",
                    list(diabop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("ℹ️", key="diab_info"):
                    show_diabetes_popup()

    with sub_col2:
        with st.container(height=h, border=True):
            st.header("Your Oral Health")

            # ------------------------
            # Halitosis
            # ------------------------
            @st.dialog("What is bad breath?")
            def show_halitosis_popup():
                st.write("""
                Bad breath, also called halitosis, means an unpleasant smell
                coming from the mouth.

                It may be related to dry mouth, tongue coating, gum disease,
                tooth decay, or oral infection.
                """)

            col1, col2 = st.columns([8, 1])

            with col1:
                hal = st.selectbox(
                    "Do you or people close to you notice bad breath? How bad from 0 (nothing) to 5 (very bad)?",
                    list(halop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ℹ️", key="hal_info"):
                    show_halitosis_popup()


            # ------------------------
            # Oral candidiasis
            # ------------------------
            @st.dialog("What is oral candidiasis?")
            def show_candidiasis_popup():
                st.write("""
                Oral candidiasis is a fungal infection that can appear inside
                the mouth.

                It may cause white patches, redness, soreness, burning,
                or a cotton-like feeling.

                Compare your symptoms with the reference image below.
                """)

                st.image("images/2.jpg", use_container_width=True)

            col1, col2 = st.columns([8, 1])

            with col1:
                cand = st.selectbox(
                    "Have you noticed any white patches, soreness, or a cotton-like feeling in your mouth?",
                    list(candop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ℹ️", key="cand_info"):
                    show_candidiasis_popup()


            # ------------------------
            # Tongue fissuring
            # ------------------------
            @st.dialog("What is tongue fissuring?")
            def show_tongue_popup():
                st.write("""
                Tongue fissuring means having deep lines, cracks, or grooves
                on the surface of the tongue.

                Food or bacteria may stay inside these grooves and cause
                discomfort, irritation, or bad breath.

                Compare your symptoms with the reference image below.
                """)

                st.image("images/3.jpg", use_container_width=True)

            col1, col2 = st.columns([8, 1])

            with col1:
                tongue = st.selectbox(
                    "Does your tongue have deep lines, cracks, or grooves?",
                    list(lendop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ℹ️", key="tongue_info"):
                    show_tongue_popup()


            # ------------------------
            # Periodontal disease
            # ------------------------
            @st.dialog("What is periodontal disease?")
            def show_periodontal_popup():
                st.write("""
                Periodontal disease, also called gum disease, affects the gums
                and the tissues supporting the teeth.

                Signs may include bleeding gums, swollen gums, bad breath,
                loose teeth, or pain when chewing.

                Compare your symptoms with the reference image below.
                """)

                st.image("images/4.jpg", use_container_width=True)

            col1, col2 = st.columns([8, 1])

            with col1:
                per = st.selectbox(
                    "Do your gums bleed, feel swollen, or do any teeth feel loose?",
                    list(perdop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ℹ️", key="per_info"):
                    show_periodontal_popup()


    with sub_col3:
        with st.container(height=h, border=True):
            st.header("Your Kidney Health")

            @st.dialog("What do CKD stages mean?")
            def show_ckd_popup():
                st.write("""
                CKD means Chronic Kidney Disease. It is commonly classified
                into stages from 1 to 5 according to how well the kidneys are
                filtering blood.

                **Stage 1:** Kidney damage is present, but kidney function is
                still normal or near normal.

                **Stage 2:** Mild decrease in kidney function.

                **Stage 3:** Moderate decrease in kidney function. Medical
                follow-up becomes especially important.

                **Stage 4:** Severe decrease in kidney function. The patient
                may need preparation for advanced treatment.

                **Stage 5:** Kidney failure. Dialysis or kidney transplant may
                be needed.

                **Dialysis:** A treatment that helps remove waste and extra
                fluid from the blood when the kidneys can no longer do this
                properly.
                """)

            col1, col2 = st.columns([8, 1])

            with col1:
                ckd = st.selectbox(
                    "What is your kidney disease stage?:",
                    list(ckdop.keys())
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("ℹ️", key="ckd_info"):
                    show_ckd_popup()



# --- CALCULATION LOGIC ---
def calculate_risk():
    total = (xerop[xer] + medop[med] + diabop[diab] + 
             halop[hal] + candop[cand] + lendop[tongue] + 
             perdop[per] + ckdop[ckd])
    st.session_state.total_points = total
    st.session_state.calculated = True

# --- RIGHT COLUMN LOGIC (Vertical Combined) ---
with col_final_right:

    with st.container(height=hf, border=True):
        
        # Determine text color based on state
        txt_col = "gray" if not st.session_state.calculated else "black"
        
        st.markdown(f"""
            <div style="color: {txt_col};">
                <h1>Risk Results</h1>
                <p>Complete all fields and press the button below to see the risk assessment.</p>
            </div>
        """, unsafe_allow_html=True)

        # Calculation Button
        if st.button("Calculate Risk Score", use_container_width=True):
            calculate_risk()

        st.divider()

        # Show results only if calculated
        if st.session_state.calculated:
            points = st.session_state.total_points
            
            if points <= 3:
                st.success(f"## Low Risk\nScore: {points}")
            elif 4 <= points <= 6:
                st.warning(f"## Moderate Risk\nScore: {points}")
            else:
                st.error(f"## High Risk\nScore: {points}")
                
            # Share button logic for Moderate/High risk
            if points >= 4:
                st.write("---")

                # --- Paso 1: Toggle para iniciar el proceso ---
                generate_report = st.toggle("Generate detailed PDF report")

                if generate_report:

                    # --- Paso 2: Datos obligatorios ---
                    st.subheader("Patient Information")

                    name = st.text_input("Full Name")
                    age = st.number_input("Age", min_value=1, max_value=120, step=1)
                    sex = st.selectbox("Sex", ["", "Male", "Female", "Other"])
                    data_consent = st.checkbox("I accept the processing of my personal data")

                    st.write("---")

                    # --- Paso 3: Validación de datos ---
                    ready_to_generate = (
                        name.strip() != "" and
                        sex != "" and
                        age > 0 and
                        data_consent
                    )

                    # --- Paso 4: Solo si todo está listo, generar PDF y mostrar botón ---
                    if ready_to_generate:

                        patient_data = [
                            {"indicator": "Dry mouth / Xerostomia", "response": xer, "score": xerop[xer]},
                            {"indicator": "Medications causing dry mouth", "response": med, "score": medop[med]},
                            {"indicator": "Diabetes", "response": diab, "score": diabop[diab]},
                            {"indicator": "Bad breath / Halitosis", "response": hal, "score": halop[hal]},
                            {"indicator": "Oral candidiasis", "response": cand, "score": candop[cand]},
                            {"indicator": "Tongue fissuring / Scrotal tongue", "response": tongue, "score": lendop[tongue]},
                            {"indicator": "Periodontal disease", "response": per, "score": perdop[per]},
                            {"indicator": "CKD stage", "response": ckd, "score": ckdop[ckd]},
                        ]

                        pdf_file = build_patient_report_pdf(patient_data, points)

                        st.download_button(
                            label="📄 Get My Report",
                            data=pdf_file,
                            file_name="oral_ckd_risk_report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                    else:
                        # Botón fantasma (no hace nada)
                        st.button(
                            "📄 Get My Report",
                            disabled=True,
                            use_container_width=True
                        )

                else:
                    st.info("Activate the switch above to generate a personalized report.")

        else:
            # Initial state: gray text
            st.markdown('<p style="color: gray;"><i>Waiting for calculation...</i></p>', unsafe_allow_html=True)
