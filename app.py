import openai
import fitz  # PyMuPDF
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

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

# Function to log query, response, and metadata to Google Sheets with truncation
def log_to_google_sheets(email, pdf_name, action, result, temperature=0.2, tokens_used=0, feedback=None):
    max_cell_length = 1000  # Limit any field text to 1,000 characters

    # Clean and truncate the response text and action
    cleaned_result = re.sub(r'[^\x00-\x7F]+', '', result)[:max_cell_length]
    cleaned_action = re.sub(r'[^\x00-\x7F]+', '', action)[:max_cell_length]
    cleaned_pdf_name = pdf_name[:max_cell_length]
    cleaned_email = email[:max_cell_length]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        sheet.append_row([timestamp, cleaned_email, cleaned_pdf_name, cleaned_action, cleaned_result, temperature, tokens_used, feedback])
    except Exception as e:
        st.error(f"An error occurred while logging to Google Sheets: {str(e)}")

# Function to extract text from uploaded PDF
def extract_text_from_pdf(file_content):
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to count tokens in the extracted text
def count_tokens(text):
    return len(text.split())

# Initialize session state for chat history, feedback, email, and token count if they don't exist
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

# Sidebar for email input, PDF uploader, and key actions
with st.sidebar:
    st.title("RFP Navigator 🧭")
    
    # Email input field
    st.session_state.email = st.text_input("Enter your email address so we can track feedback")

    if st.session_state.email:
        # PDF uploader
        uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

        if uploaded_file and uploaded_file.name != st.session_state.pdf_name:
            # Extract text from the PDF and store it in session state
            extracted_text = extract_text_from_pdf(uploaded_file.read())
            token_count = count_tokens(extracted_text)
            st.session_state.extracted_text = extracted_text
            st.session_state.pdf_name = uploaded_file.name  # Track the PDF name to avoid reprocessing

            # Log the PDF upload to Google Sheets
            log_to_google_sheets(
                email=st.session_state.email,
                pdf_name=uploaded_file.name,
                action="PDF Uploaded",
                result=f"PDF loaded and text extracted.",
                tokens_used=token_count,
                temperature=0.0  # Use 0.0 to indicate this is not a typical query
            )

            # Convert token count to thousands (k)
            token_count_k = token_count / 1000

            # Display success message with a hard return between text extracted and token count
            st.success(f"PDF loaded and text extracted.\n\nToken count: {token_count_k:.1f}k/128k")

            st.markdown('---')
            st.subheader("**Key Actions**")

        # Ensure the extracted text is available before proceeding
        if st.session_state.extracted_text:
            # Button to generate the executive summary
            if st.button("Generate Executive Summary"):
                try:
                    summary_template = """
                    Create an executive summary of this RFP document tailored for an executive architectural designer. Include key dates (issue date, response due date, and selection date), a project overview, the scope of work, a list of deliverables, Selection Criteria, and other important information. Conclude with a brief one-sentence summary identifying specific areas in the RFP where it aligns with Perkins&Will's core values, such as Design Excellence, Living Design, Sustainability, Resilience, Research, Diversity and Inclusion, Social Purpose, Well-Being, and Technology, with specific examples from the document.
                    """

                    st.session_state.messages.append({"role": "user", "content": "Please generate an executive summary based on the RFP document."})
                    
                    # Generate response using OpenAI's new SDK method
                    response = openai.Client().chat.completions.create(
                        model="gpt-4o-mini",  # Use a model you have access to
                        messages=st.session_state.messages + [{"role": "user", "content": summary_template.format(extracted_text=st.session_state.extracted_text)}],  # Include chat history and query with full context
                        max_tokens=2048,
                        temperature=0.2,
                        top_p=1.0,
                        frequency_penalty=0.0,
                        presence_penalty=0.0
                    )

                    response_content = response.choices[0].message.content.strip()
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                    # Calculate tokens used for this response
                    tokens_used = count_tokens(response_content)

                    # Log the action to Google Sheets with tokens used
                    log_to_google_sheets(st.session_state.email, uploaded_file.name, "Generate Executive Summary", response_content, temperature=0.2, tokens_used=tokens_used)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

            # Button to generate pipeline data
            if st.button("Generate Pipeline Data"):
                try:
                    pipeline_template = """
                    Extract and present the following key data points from this RFP document in a table format for CRM entry:
                    - Client Name
                    - Opportunity Name
                    - Primary Contact (name, title, email, and phone)
                    - Primary Practice (select from: Branded Environments, Corporate and Commercial, Corporate Interiors, Cultural and Civic, Health, Higher Education, Hospitality, K-12 Education, Landscape Architecture, Planning & Strategies, Science and Technology, Single Family Residential, Sports Recreation and Entertainment, Transportation, Urban Design, Unknown / Other)
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
                    
                    Additional Information Aligned with Core Values:
                    - Design Excellence Opportunities
                    - Sustainability Initiatives
                    - Resilience Measures
                    - Innovation Potential
                    - Diversity and Inclusion Aspects
                    - Social Purpose Contributions
                    - Well-Being Factors
                    - Technological Integration Points
                    
                    If the information is not found, respond with 'Sorry, I could not find that information.'

                    RFP Document Text:
                    {extracted_text}
                    """

                    response = openai.Client().chat.completions.create(
                        model="gpt-4o-mini",  # Use a model you have access to
                        messages=st.session_state.messages + [
                            {"role": "user", "content": pipeline_template.format(extracted_text=st.session_state.extracted_text)}
                        ],  # Include chat history and query with full context
                        max_tokens=2048,
                        temperature=0.2,
                        top_p=1.0,
                        frequency_penalty=0.0,
                        presence_penalty=0.0
                    )

                    response_content = response.choices[0].message.content.strip()
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                    # Calculate tokens used for this response
                    tokens_used = count_tokens(response_content)

                    # Log the action to Google Sheets with tokens used
                    log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, "Generate Pipeline Data", response_content, temperature=0.2, tokens_used=tokens_used)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# Main window for chat interaction
st.title("RFP Navigator 🧭")

# Initial screen when no PDF is uploaded or no email entered
if not st.session_state.email:
    st.write("Please enter your email address in the sidebar to start.")
elif not uploaded_file:
    st.write("Please load your RFP in the side window.\n\nRemember, this is generative AI and is experimental.")
else:
    # Display chat messages and add thumbs up/down buttons
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])

            if message["role"] == "assistant":
                # Display thumbs-up and thumbs-down side by side in the same column with reduced gap
                col1, col2 = st.columns([0.08, 1])
                with col1:
                    if st.button("👍", key=f"thumbs_up_{i}", help="Was this Helpful?"):
                        st.session_state.feedback[message['content']] = "Thumbs Up"
                        log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, message["content"], "Thumbs Up")
                with col2:
                    if st.button("👎", key=f"thumbs_down_{i}", help="Was this Helpful?"):
                        st.session_state.feedback[message['content']] = "Thumbs Down"
                        log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, message["content"], "Thumbs Down")

    # User input for chat
    if prompt := st.chat_input("Ask a question or request data from the RFP"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response immediately after user input
        try:
            query_template = f"""
            Based on the provided document, answer the following question: '{prompt}'. 
            Provide a concise and accurate response. 
            If the information is not explicitly mentioned, provide relevant context or suggest an appropriate next step.
            """
            
            response = openai.Client().chat.completions.create(
                model="gpt-4o-mini",  # Use a model you have access to
                messages=st.session_state.messages + [{"role": "user", "content": query_template.format(st.session_state.extracted_text)}],  # Include chat history and query with full context
                max_tokens=2048,  # Adjust this value as needed between 150-300
                temperature=0.2,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )

            response_content = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            with st.chat_message("assistant"):
                st.write(response_content)

            # Calculate tokens used for this response
            tokens_used = count_tokens(response_content)

            # Log the action to Google Sheets with tokens used
            log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, prompt, response_content, temperature=0.2, tokens_used=tokens_used)

            # Add thumbs-up and thumbs-down buttons for the response
            col1, col2 = st.columns([0.08, 1])
            with col1:
                if st.button("👍", key=f"thumbs_up_{len(st.session_state.messages)}", help="Was this Helpful?"):
                    st.session_state.feedback[response_content] = "Thumbs Up"
                    log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, response_content, "Thumbs Up")
            with col2:
                if st.button("👎", key=f"thumbs_down_{len(st.session_state.messages)}", help="Was this Helpful?"):
                    st.session_state.feedback[response_content] = "Thumbs Down"
                    log_to_google_sheets(st.session_state.email, st.session_state.pdf_name, response_content, "Thumbs Down")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
