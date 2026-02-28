import streamlit as st
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from datetime import date
from pypdf import PdfReader # For PDF support

# --- 1. PDF ENGINE & DETAILED DISCLAIMER ---
class CRE_PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        footer_text = "CONFIDENTIAL LEGAL COMMUNICATION - FOR SETTLEMENT PURPOSES ONLY"
        self.cell(0, 10, f"{footer_text} | Page {self.page_no()}", 0, 0, 'C')

def display_disclaimer():
    st.divider()
    st.markdown(
        """
        <style>
        .disclaimer { font-size: 10px; color: #888888; line-height: 1.2; text-align: justify; }
        </style>
        <div class="disclaimer">
            <strong>LEGAL DISCLAIMER:</strong> This tool is an AI-powered administrative assistant and does not constitute 
            legal, financial, or environmental advice. All outputs must be reviewed by licensed legal counsel.
        </div>
        """,
        unsafe_allow_html=True
    )

# --- 2. LOGIC FUNCTIONS ---
# FIXED: Added property_address to arguments to prevent Line 47 error
def generate_objection_letter(findings, property_address, buyer_name):
    # On Streamlit Cloud, it will look for the API key in st.secrets automatically
    llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"""
    Draft a formal CRE Objection Letter for {property_address} on behalf of {buyer_name}.
    Based on these findings: {findings}.
    Tone: Sophisticated, Legal and firm. 
    Include standard legal placeholders for [DATE] and [SELLER NAME].
    """
    return llm.invoke(prompt).content

# --- 3. PASSWORD PROTECTION GATE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 CRE Agent Login")
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        
        if st.button("Log In"):
            if "passwords" in st.secrets and user_input in st.secrets["passwords"]:
                if pass_input == st.secrets["passwords"][user_input]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password.")
            else:
                st.error("❌ Username not recognized.")
            
            st.info("Forgot access? Contact: admin@yourdomain.com")
        return False
    return True

# --- 4. MAIN APP ---
if check_password():
    with st.sidebar:
        st.title("Deal Dashboard")
        if st.button("Log Out"):
            del st.session_state["password_correct"]
            st.rerun()
        
        st.divider()
        prop_addr = st.text_input("Property Address", "123 Industrial Way")
        buyer = st.text_input("Buyer Entity", "Acme Holdings LLC")

    st.title("🏢 CRE Closing Orchestrator")
    uploaded_file = st.file_uploader("Upload Document (PDF or TXT)", type=["txt", "pdf"])

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            doc_text = "".join([page.extract_text() for page in reader.pages])
        else:
            doc_text = uploaded_file.read().decode("utf-8")
        
        if st.button("🚀 Run AI Audit"):
            with st.spinner("Analyzing risk..."):
                llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
                audit_prompt = f"Analyze this for CRE risk. Use [RED], [YELLOW], or [GREEN] tags: {doc_text}"
                st.session_state['last_audit'] = llm.invoke(audit_prompt).content

    if 'last_audit' in st.session_state:
        audit_res = st.session_state['last_audit']
        if "[RED]" in audit_res: st.error(audit_res.replace("[RED]", "🔴 CRITICAL:"))
        elif "[YELLOW]" in audit_res: st.warning(audit_res.replace("[YELLOW]", "🟡 NEGOTIABLE:"))
        else: st.success(audit_res.replace("[GREEN]", "🟢 CLEAR:"))

        if st.button("📝 Generate Objection Letter"):
            with st.spinner("Drafting..."):
                st.session_state['last_letter'] = generate_objection_letter(audit_res, prop_addr, buyer)

    if 'last_letter' in st.session_state:
        st.divider()
        st.session_state['last_letter'] = st.text_area("Edit Letter", value=st.session_state['last_letter'], height=300)
        
        # PDF Generation
        pdf = CRE_PDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "FORMAL OBJECTION NOTICE", 0, 1, 'C')
        pdf.set_font("Arial", size=11)
        
        # Encoding fix for PDF
        clean_text = st.session_state['last_letter'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=f"Objection_Notice.pdf",
            mime="application/pdf"
        )

    display_disclaimer()
