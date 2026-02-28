import streamlit as st
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import date
import os

load_dotenv()

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
        .disclaimer {
            font-size: 10px;
            color: #888888;
            line-height: 1.2;
            text-align: justify;
        }
        </style>
        <div class="disclaimer">
            <strong>LEGAL DISCLAIMER:</strong> This tool is an AI-powered administrative assistant and does not constitute 
            legal, financial, or environmental advice. The "Objection Letter" and "Audit Results" are drafts generated for 
            informational purposes only. Users must have all outputs reviewed and approved by licensed legal counsel 
            prior to execution or delivery. Use of this software does not create an attorney-client relationship. 
            The developers assume no liability for errors, omissions, or the consequences of any actions taken based 
            on the information provided by this agent.
        </div>
        """,
        unsafe_allow_html=True
    )

# --- 2. LOGIC FUNCTIONS ---
def generate_objection_letter(findings, buyer_name):
    llm = ChatOpenAI(model="gpt-4o")
    # We use a placeholder [PROPERTY_ADDRESS] so we can swap it later
    prompt = f"""
    Draft a formal CRE Objection Letter for {property_address} on behalf of {buyer_name}.
    Property Address: [PROPERTY_ADDRESS]
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
            # This checks if the passwords section exists in secrets
            if "passwords" in st.secrets:
                # This checks if the username exists in that section
                if user_input in st.secrets["passwords"]:
                    # This checks if the password matches
                    if pass_input == st.secrets["passwords"][user_input]:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password.")
                else:
                    st.error("❌ Username not recognized.")
            else:
                st.error("❌ Critical Error: Secrets file not found or '[passwords]' header missing.")
            
            # THE FORGOT PASSWORD HOOK
            st.info("Forgot access? Contact: admin@yourdomain.com")
            
        return False
    return True

# --- 4. MAIN APP (Must be indented under the password check) ---
if check_password():
    # Sidebar Setup
    with st.sidebar:
        st.title("Deal Dashboard")
        if st.button("Log Out"):
            del st.session_state["password_correct"]
            st.rerun()
        
        st.subheader("⏳ Transaction Timeline")
        dd_end_date = st.date_input("Due Diligence Deadline", date(2026, 4, 15))
        days_left = (dd_end_date - date.today()).days
        
        if days_left > 0:
            st.metric(label="Days to DD Deadline", value=f"{days_left} Days")
            st.progress(max(0, min(100, (100 - (days_left * 2)))))
        else:
            st.error("⚠️ DUE DILIGENCE EXPIRED")

        st.divider()
        prop_addr = st.text_input("Property Address", "123 Industrial Way")
        buyer = st.text_input("Buyer Entity", "Acme Holdings LLC")

    st.title("🏢 CRE Closing Orchestrator")
    uploaded_file = st.file_uploader("Upload Document (Text only)", type=["txt"])

    if uploaded_file:
        doc_text = uploaded_file.read().decode("utf-8")
        
        if st.button("🚀 Run AI Audit"):
            with st.spinner("Analyzing legal risks..."):
                llm = ChatOpenAI(model="gpt-4o")
                audit_prompt = f"Analyze this for CRE risk. Categorize using [RED], [YELLOW], or [GREEN] tags: {doc_text}"
                st.session_state['last_audit'] = llm.invoke(audit_prompt).content

    # PERSISTENT AUDIT DISPLAY
    if 'last_audit' in st.session_state:
        audit_res = st.session_state['last_audit']
        st.markdown("### 📋 Audit Findings")
        if "[RED]" in audit_res: st.error(audit_res.replace("[RED]", "🔴 CRITICAL:"))
        elif "[YELLOW]" in audit_res: st.warning(audit_res.replace("[YELLOW]", "🟡 NEGOTIABLE:"))
        else: st.success(audit_res.replace("[GREEN]", "🟢 CLEAR:"))

       if st.button("📝 Generate Objection Letter"):
            with st.spinner("Drafting legal notice..."):
                # We pass: 1. The Audit, 2. The Address, 3. The Buyer
                st.session_state['last_letter'] = generate_objection_letter(
                    st.session_state['last_audit'], 
                    prop_addr, 
                    buyer
                )

    # PERSISTENT LETTER & DOWNLOAD DISPLAY
    if 'last_letter' in st.session_state:
        st.divider()
        st.subheader("Draft Objection Letter")

        # GET THE CURRENT LETTER FROM STATE
        current_letter = st.session_state['last_letter']

        # DYNAMIC SWAP: Replace the placeholder with whatever is CURRENTLY in the sidebar
        # This makes the letter respond to sidebar changes instantly!
        display_letter = current_letter.replace("[PROPERTY_ADDRESS]", prop_addr)

        # EDITABLE TEXT AREA
        # We store the edited version back to session state
        st.session_state['last_letter'] = st.text_area(
            "Legal Draft (Editable)", 
            value=display_letter, 
            height=400
        )
        # Prepare PDF
        pdf = CRE_PDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "FORMAL OBJECTION NOTICE", 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font("Arial", size=11)
        
        # Clean text for FPDF compatibility
        clean_text = st.session_state['last_letter'].replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
        clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 10, clean_text)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 Download Legal-Ready PDF",
            data=pdf_bytes,
            file_name=f"Objection_Letter_{prop_addr.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

    # The detailed legal disclaimer always shows at the bottom of the logged-in app
    display_disclaimer()



