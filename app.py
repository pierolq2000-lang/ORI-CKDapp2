import streamlit as st

st.set_page_config(layout="wide")

# --- DATA DICTIONARIES ---
xerop = {"No": 0, "Sometimes": 1, "Always": 2}
medop = {"No": 0, "Yes": 1}
diabop = {"No": 0, "Yes": 1}

halop = {"0": 1, "1": 1, "2": 2, "3": 2, "4": 3, "5": 3}
candop = {"No": 0, "Yes": 2}
lendop = {"No": 0, "Yes": 1}
perdop = {"None": 0, "Moderate": 1, "Severe": 2}

ckdop = {"0": 0, "1": 0, "2": 0, "3": 1, "4": 2, "5": 2, "Dialysis": 3}

h = 460

# Initialize calculation state if it doesn't exist
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
    st.session_state.total_points = 0 

# Create main columns (3:1 ratio)
col_main_left, col_final_right = st.columns([3, 1])

# --- LEFT COLUMN LOGIC ---
with col_main_left:
    # Row 1: Title (Spans across 3 sub-columns)
    st.title('Oral Health Index & CKD Risk Calculator')
    st.text('This calculator aims to estimate the percentage risk by which a patient’s oral health status may contribute to the development or progression of chronic kidney disease (CKD).')

    # Row 2: Split into 3 sub-columns
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    
    with sub_col1:
        with st.container(height=h, border=True):
            st.header("Patient")
            xer = st.selectbox("Xerostomia:", list(xerop.keys()), help="Subjective feeling of dry mouth")
            med = st.selectbox("Medications causing dry mouth:", list(medop.keys()), help="Diuretics or Antihypertensives")
            diab = st.selectbox("Diabetes:", list(diabop.keys()), help="Either Type 1 or 2")

    with sub_col2:
        with st.container(height=h, border=True):
            st.header("Dental Exam")
            hal = st.selectbox("Halitosis:", list(halop.keys()), help="Unpleasant mouth odor")
            cand = st.selectbox("Candidiasis:", list(candop.keys()), help="A fungal infection (Candida Albicans)")
            tongue = st.selectbox("Tongue Fissuring / Scrotal Tongue:", list(lendop.keys()), help="Grooves or cracks on tongue surface")
            per = st.selectbox("Periodontal Disease:", list(perdop.keys()), help="Disease of gums and supporting bone")

    with sub_col3:
        with st.container(height=h, border=True):
            st.header("CKD")
            ckd = st.selectbox("CKD Stage:", list(ckdop.keys()), help="Severity of kidney disease (based on GFR)")

# --- CALCULATION LOGIC ---
def calculate_risk():
    total = (xerop[xer] + medop[med] + diabop[diab] + 
             halop[hal] + candop[cand] + lendop[tongue] + 
             perdop[per] + ckdop[ckd])
    st.session_state.total_points = total
    st.session_state.calculated = True

# --- RIGHT COLUMN LOGIC (Vertical Combined) ---
with col_final_right:

    with st.container(height=615, border=True):
        
        # Determine text color based on state
        txt_col = "gray" if not st.session_state.calculated else "black"
        
        st.markdown(f"""
            <div style="color: {txt_col};">
                <h1>Calculator Results</h1>
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
                st.button("📤 Share Results", use_container_width=True, help="Sharing feature coming soon")

        else:
            # Initial state: gray text
            st.markdown('<p style="color: gray;"><i>Waiting for calculation...</i></p>', unsafe_allow_html=True)
