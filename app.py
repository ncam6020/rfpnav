import openai
import fitz  # PyMuPDF
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Load the OpenAI API key from secrets
api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = api_key

# Set up the page configuration
st.set_page_config(page_title="RFP Navigator", page_icon="🧭")

# Initialize Google Sheets client
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["connections"]["gsheets"], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1
    return sheet

sheet = connect_to_google_sheets()

def log_to_google_sheets(pdf_name, action, result, feedback=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, pdf_name, action, result, feedback])

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help navigate your RFP?"}]
if "history" not in st.session_state:
    st.session_state.history = []
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = {}

# Function to extract text from uploaded PDF
def extract_text_from_pdf(file_content):
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to split text into chunks that fit within the token limit
def split_text_into_chunks(text, chunk_size=1500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

# Function to get the system message
def get_system_message():
    return {
        "role": "system",
        "content": "Enable executives at Perkins&Will to swiftly and accurately analyze RFP documents, highlighting crucial information needed for go/no-go decisions and facilitating the initial steps of proposal development. If you cannot find the required information, respond with 'Sorry, I could not find that information.'"
    }

# General function to handle any prompt
def handle_prompt(pdf_name, text, prompt_template, temperature):
    combined_text = " ".join(split_text_into_chunks(text))
    prompt = prompt_template.format(combined_text=combined_text)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[get_system_message(), {"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=temperature  # Use the temperature from the slider
        )
        result = response['choices'][0]['message']['content'].strip()
        st.session_state.feedback[result] = None  # Initialize feedback state
        log_to_google_sheets(pdf_name, prompt, result)  # Log the action and result to Google Sheets
        return result
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "An error occurred while processing the request."

# Sidebar for PDF uploader, temperature slider, and feedback
with st.sidebar:
    st.title("RFP Navigator 🧭")
    st.markdown('---')
    uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], key="file_uploader")

    # Add temperature slider with hover text
    temperature = st.slider(
        "Set Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.05,
        help="Temperature controls the randomness of the model's responses. Lower values (e.g., 0.1) make the output more focused and deterministic, while higher values (e.g., 1.0) make it more creative and varied."
    )
    
    if uploaded_file:
        # Extract text from the PDF and store it in session state
        st.session_state.extracted_text = extract_text_from_pdf(uploaded_file.read())
        pdf_name = uploaded_file.name  # Capture the file name

        st.markdown('---')
        st.subheader("**Key Actions**")

        if st.button("Generate Executive Summary"):
            action_text = "Generate Executive Summary"
            st.session_state.messages.append({"role": "user", "content": action_text})

            summary_template = """
            Create an executive summary of this RFP document tailored for an executive architectural designer. Include key dates (issue date, response due date, and selection date), a project overview, the scope of work, and a list of deliverables. Conclude with a brief two-sentence summary identifying specific areas in the RFP where it aligns with Perkins&Will's core values, such as Design Excellence, Living Design, Sustainability, Resilience, Research, Diversity and Inclusion, Social Purpose, Well-Being, and Technology, with specific examples from the document.

            RFP Document Text:
            {combined_text}
            """

            summary = handle_prompt(pdf_name, st.session_state.extracted_text, summary_template, temperature)
            st.session_state.messages.append({"role": "assistant", "content": summary})

        if st.button("Gather Pipeline Data"):
            action_text = "Gather Pipeline Data"
            st.session_state.messages.append({"role": "user", "content": action_text})

            crm_data_template = """
            Extract and present the following key data points from this RFP document in a table format for CRM entry:
            - Client Name
            - Opportunity Name
            - Primary Contact (name, title, email, and phone)
            - Primary Practice (select from: Branded Environments, Corporate and Commercial, Corporate Interiors, Cultural and Civic, Health, Higher Education, Hospitality, K-12 Education, Landscape Architecture, Planning&Strategies, Science and Technology, Single Family Residential, Sports Recreation and Entertainment, Transportation, Urban Design, Unknown / Other)
            - Discipline (select from: Arch/Interior Design, Urban Design, Landscape Arch, Advisory Services, Branded Environments, Unknown / Other)
            - City
            - Country
            - RFP Release Date
            - Proposal Due Date
            - Interview Date
            - Selection Date
            - Design Start Date
            - Design Completion Date
            - Construction Start Date
            - Construction Completion Date
            - Project Description
            - Scopes (select from: New, Renovation, Addition, Building Repositioning, Competition, Infrastructure, Master Plan, Planning, Programming, Replacement, Study, Unknown / Other)
            - Program Type (select from: Civic and Cultural, Corporate and Commercial, Sports, Recreation + Entertainment, Education, Residential, Science + Technology, Transportation, Misc, Urban Design, Landscape Architecture, Government, Social Purpose, Health, Unknown / Other)
            - Delivery Type (select from: Construction Manager at Risk (CMaR), Design Only, Design-Bid-Build, Design-Build, Integrated Project Delivery (IPD), Guaranteed Maximum Price (GMP), Joint Venture (JV), Public Private Partnership (P3), Other)
            - Estimated Program Area
            - Estimated Budget
            - Sustainability Requirement
            
            If the information is not found, respond with 'Sorry, I could not find that information.'

            RFP Document Text:
            {combined_text}
            """
            crm_data = handle_prompt(pdf_name, st.session_state.extracted_text, crm_data_template, temperature)
            st.session_state.messages.append({"role": "assistant", "content": crm_data})

# Display chat messages and add thumbs up/down buttons
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant":
            # Display thumbs-up and thumbs-down side by side in the same column with reduced gap
            col1, col2 = st.columns([0.08, 1])
            with col1:
                if st.button("👍", key=f"thumbs_up_{message['content']}", help="Was this Helpful?"):
                    st.session_state.feedback[message['content']] = "Thumbs Up"
                    log_to_google_sheets(pdf_name, message["content"], "Thumbs Up")
            with col2:
                if st.button("👎", key=f"thumbs_down_{message['content']}", help="Was this Helpful?"):
                    st.session_state.feedback[message['content']] = "Thumbs Down"
                    log_to_google_sheets(pdf_name, message["content"], "Thumbs Down")

# User-provided prompt
if prompt := st.chat_input("Search your RFP"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from OpenAI
    response = handle_prompt(pdf_name, st.session_state.extracted_text, f"Based on the RFP document text provided below, please answer the following query: {prompt}\n\nRFP Document Text:\n{{combined_text}}", temperature)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
