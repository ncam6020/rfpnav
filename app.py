import openai
import fitz  # PyMuPDF
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import time

# Constants
MAX_TOKENS = 2048
TEMPERATURE = 0.2
MODEL_NAME = "gpt-4o-mini"

# Load the OpenAI API key and set up the page configuration
openai.api_key = st.secrets["OPENAI_API_KEY"]
st.set_page_config(page_title="RFP Navigator", page_icon="🧭")

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = {}
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = ""

# Google Sheets Setup
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["connections"]["gsheets"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1

sheet = connect_to_google_sheets()

# Logging Function
def log_to_google_sheets(email, pdf_name, action, result, tokens_used=0, feedback=None):
    def clean_text(text):
        return re.sub(r'[^\x00-\x7F]+', '', text)[:1000]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        timestamp,
        clean_text(email),
        clean_text(pdf_name),
        clean_text(action),
        clean_text(result),
        TEMPERATURE,
        tokens_used,
        feedback
    ]
    try:
        sheet.append_row(row)
    except Exception as e:
        st.error(f"An error occurred while logging to Google Sheets: {str(e)}")

# PDF Extraction Function
def extract_text_from_pdf(file_content):
    doc = fitz.open(stream=file_content, filetype="pdf")
    return "\n".join(
        [f"--- Page {i+1} ---\n{page.get_text()}" for i, page in enumerate(doc)]
    )

# AI Generation Function
def generate_ai_response(template, action_label):
    try:
        response = openai.Client().chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages + [{"role": "user", "content": template}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        response_content = response.choices[0].message.content.strip()
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        tokens_used = len(response_content.split())
        log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, action_label, response_content, tokens_used=tokens_used)
        return response_content
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Button Handlers
def handle_generate_summary():
    summary_template = f"""
    Create an executive summary of this RFP document tailored for an executive architectural designer. Include key dates (issue date, response/submission due date, selection date, other important dates and times), a project overview, the scope of work, a list of deliverables, Selection Criteria, and other important information. Conclude with a concise and brief one-sentence summary identifying specific areas in the RFP where it may align with Perkins&Will's core values, such as Design Excellence, Living Design, Sustainability, Resilience, Research, Diversity and Inclusion, Social Purpose, Well-Being, and Technology, with specific examples from the document.

    RFP Document Text:
    {st.session_state.extracted_text}
    """
    generate_ai_response(summary_template, "Generate Executive Summary")

def handle_generate_pipeline_data():
    pipeline_template = f"""
    Extract and present the following key data points from this RFP document in a table format for CRM entry:
    - Client Name
    - Opportunity Name
    - Primary Contact (name, title, email, and phone)
    - Primary Practice (select from: Branded Environments, Corporate and Commercial, Corporate Interiors, Cultural and Civic, Health, Higher Education, Hospitality, K-12 Education, Landscape Architecture, Planning & Strategies, Science and Technology, Single Family Residential, Sports Recreation and Entertainment, Transportation, Urban Design, Unknown / Other)
    - Discipline (select from: Arch/Interior Design, Urban Design, Landscape Arch, Advisory Services, Branded Environments, Unknown / Other)
    - City
    - State / Province
    - Country
    - RFP Release Date
    - Proposal Due Date
    - Interview Date
    - Selection Date
    - Design Start Date
    - Design Completion Date
    - Construction Start Date
    - Construction Completion Date
    - Project Description (concise one sentence description)
    - Scope(s) of Work (select from: New, Renovation, Addition, Building Repositioning, Competition, Infrastructure, Master Plan, Planning, Programming, Replacement, Study, Unknown / Other)
    - Program Type(s) (select from: Civic and Cultural, Corporate and Commercial, Sports, Recreation + Entertainment, Education, Residential, Science + Technology, Transportation, Misc, Urban Design, Landscape Architecture, Government, Social Purpose, Health, Unknown / Other)
    - Delivery Type (select from: Construction Manager at Risk (CMaR), Design Only, Design-Bid-Build, Design-Build, Integrated Project Delivery (IPD), Guaranteed Maximum Price (GMP), Joint Venture (JV), Public Private Partnership (P3), Other)
    - Estimated Program Area
    - Estimated Budget
    - Sustainability Requirement
    - BIM Requirements

    Additional Information Aligned with Core Values:
    - Design Excellence Opportunities
    - Sustainability Initiatives
    - Resilience Measures
    - Innovation Potential
    - Diversity and Inclusion Aspects
    - Social Purpose Contributions
    - Well-Being Factors
    - Technological Innovation Opportunities
    
    If the information is not found, respond with 'Sorry, I could not find that information.'

    RFP Document Text:
    {st.session_state.extracted_text}
    """
    generate_ai_response(pipeline_template, "Generate Pipeline Data")

# Sidebar UI
def render_sidebar():
    st.sidebar.title("RFP Navigator 🧭")
    st.session_state.email = st.sidebar.text_input("Enter your email address so we can track feedback")

    if st.session_state.email:
        uploaded_file = st.sidebar.file_uploader("Upload your PDF", type=["pdf"])

        # Only extract PDF content if a new file is uploaded or if it's not already in session state
        if uploaded_file and uploaded_file.name != st.session_state.pdf_name:
            extracted_text = extract_text_from_pdf(uploaded_file.read())
            st.session_state.extracted_text = extracted_text
            st.session_state.pdf_name = uploaded_file.name

            log_to_google_sheets(
                email=st.session_state.email,
                pdf_name=uploaded_file.name,
                action="PDF Uploaded",
                result="PDF loaded and text extracted.",
                tokens_used=len(extracted_text.split())
            )
            
             # Uncomment to allow downloading the extracted text
            # st.sidebar.download_button(
            #     label="Download extracted text by pages",
            #     data=extracted_text,
            #     file_name="extracted_text_by_pages.txt",
            #     mime="text/plain"
            # )

            st.sidebar.markdown('---')

        # Ensure extracted text is available for actions
        if st.session_state.extracted_text:
            st.sidebar.subheader("**Key Actions**")
            if st.sidebar.button("Generate Executive Summary"):
                handle_generate_summary()

            if st.sidebar.button("Generate Pipeline Data"):
                handle_generate_pipeline_data()

# Main Content Window UI
def render_main_ui():
    st.title("RFP Navigator 🧭")

    if not st.session_state.email:
        st.write("Please enter your email address and upload an RFP in the sidebar to start. \n\nRemember, this is generative AI and is experimental.")
    elif not st.session_state.pdf_name:
        st.write("Please load your RFP in the sidebar.\n\nRemember, this is generative AI and is experimental.")
    else:
        st.markdown('---')
        st.subheader("**Chat Interface**")

        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.write(message["content"])

                if message["role"] == "assistant":
                    col1, col2 = st.columns([0.08, 1])
                    with col1:
                        if st.button("👍", key=f"thumbs_up_{i}", help="Was this Helpful?"):
                            st.session_state.feedback[message['content']] = "Thumbs Up"
                            log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, message["content"], "Thumbs Up")
                    with col2:
                        if st.button("👎", key=f"thumbs_down_{i}", help="Was this Helpful?"):
                            st.session_state.feedback[message['content']] = "Thumbs Down"
                            log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, message["content"], "Thumbs Down")

        if st.session_state.extracted_text:
            if prompt := st.chat_input("Ask a question or request data from the RFP"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                query_template = f"""
                Based on the provided document, answer the following question: '{prompt}'. 
                Provide a concise and accurate response. 
                If the information is not explicitly mentioned, provide relevant context or suggest an appropriate next step.

                RFP Document Text:
                {st.session_state.extracted_text}
                """
                response_content = generate_ai_response(query_template, prompt)
                if response_content:
                    with st.chat_message("assistant"):
                        st.write(response_content)

# Run the App
render_sidebar()
render_main_ui()
