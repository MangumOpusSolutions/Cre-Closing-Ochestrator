import streamlit as st
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import date
import os

## needs to fix the log in screen and password
## download button is missing from the end of the pdf ready 
## upload to streamlit and Github

def check_password():
    """Returns True if the user had the correct password."""


    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username and password.
        st.title("🔐 CRE Agent Login")
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.info("Please log in to access the Closing Orchestrator.")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show error + re-render prompt.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not found or password incorrect")
        return False
    else:
        # Password correct.
        return True

load_dotenv()

# --- 1. LOGIC FUNCTIONS ---
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

def generate_objection_letter(findings, property_address, buyer_name):
    llm = ChatOpenAI(model="gpt-4o")
    prompt = f"""
    Draft a formal CRE Objection Letter for {property_address} on behalf of {buyer_name}.
    Findings: {findings}.
    Tone: Legal, firm, demanding cure. 
    Include standard legal placeholders for [DATE] and [SELLER NAME].
    """
    return llm.invoke(prompt).content

if check_password():

# --- 2. THE PDF ENGINE (With Confidentiality Footer) ---

        class CRE_PDF(FPDF):
            def footer(self):
        # Position at 1.5 cm from bottom
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
        # Confidentiality Footer
                footer_text = "CONFIDENTIAL LEGAL COMMUNICATION - FOR SETTLEMENT PURPOSES ONLY"
                self.cell(0, 10, f"{footer_text} | Page {self.page_no()}", 0, 0, 'C')

# --- 3. UI & SIDEBAR TIMELINE ---

st.set_page_config(page_title="Closing Orchestrator", page_icon="🏢")

with st.sidebar:
    st.success(f"Logged in as Authorized User")
    if st.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()
    st.title("Deal Dashboard")
    
    # Timeline Tracker
    st.subheader("⏳ Transaction Timeline")
    closing_date = st.date_input("Target Closing Date", date(2026, 6, 1))
    dd_end_date = st.date_input("Due Diligence Deadline", date(2026, 4, 15))
    
    # Calculate Days Remaining
    today = date.today()
    days_left = (dd_end_date - today).days
    
    if days_left > 0:
        st.metric(label="Days to DD Deadline", value=f"{days_left} Days")
        progress = max(0, min(100, (100 - (days_left * 2)))) # Visual progress bar
        st.progress(progress / 100)
    else:
        st.error("⚠️ DUE DILIGENCE EXPIRED")

    st.divider()
    prop_addr = st.text_input("Property Address", "123 Industrial Way")
    buyer = st.text_input("Buyer Entity", "Acme Holdings LLC")

# --- 4. MAIN APP INTERFACE ---

st.title("🏢 CRE Closing Orchestrator")
uploaded_file = st.file_uploader("Upload Document", type=["txt"])

if uploaded_file:
    doc_text = uploaded_file.read().decode("utf-8")
    
    if st.button("🚀 Run AI Audit"):
        with st.spinner("Agent analyzing risk levels..."):
            llm = ChatOpenAI(model="gpt-4o")
            # We specifically ask for the color tags here
            prompt = f"""
            Analyze this for CRE risk: {doc_text}
            Categorize your findings using exactly one of these headers at the start:
            - [RED]: For critical deal killers/RECs.
            - [YELLOW]: For negotiable risks/credits.
            - [GREEN]: For standard/clear items.
            Provide a concise summary of why you chose that color.
            """
            result = llm.invoke(prompt).content
            st.session_state['last_audit'] = result 

    # Logic to show the colored boxes based on the AI's response
    if 'last_audit' in st.session_state:
        audit_output = st.session_state['last_audit']
        
        st.markdown("### 📋 Audit Results")
        if "[RED]" in audit_output:
            st.error(audit_output.replace("[RED]", "🔴 CRITICAL RISK FOUND:"))
        elif "[YELLOW]" in audit_output:
            st.warning(audit_output.replace("[YELLOW]", "🟡 NEGOTIABLE RISK:"))
        else:
            st.success(audit_output.replace("[GREEN]", "🟢 CLEAR / STANDARD:"))

        if 'last_audit' in st.session_state:
         if st.button("📝 Generate Objection Letter"):
            with st.spinner("Drafting legal notice..."):
                letter = generate_objection_letter(st.session_state['last_audit'], prop_addr, buyer)
                # Store it so it stays on screen
                st.session_state['last_letter'] = letter

        # Check if the letter exists in memory
        if 'last_letter' in st.session_state:
            st.subheader("Edit Objection Letter")
            # Update memory if user edits the text area
            updated_letter = st.text_area("Legal Draft (Editable)", 
                                         value=st.session_state['last_letter'], 
                                         height=400)
            st.session_state['last_letter'] = updated_letter

            # PDF Generation Logic
            pdf = CRE_PDF()
            pdf.add_page()
            
            # Add a Header to the PDF
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "OBJECTION NOTICE", 0, 1, 'C')
            pdf.ln(5)
            
            # Body Text
            pdf.set_font("Arial", size=11)
            clean_text = st.session_state['last_letter'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.download_button(
                label="📥 Download Legal-Ready PDF",
                data=pdf_bytes,
                file_name=f"Objection_Notice_{prop_addr.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

# Always keep this at the very bottom
display_disclaimer()

    