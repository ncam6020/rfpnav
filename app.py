import openai
import fitz  # PyMuPDF
import streamlit as st
import json
import os
from datetime import datetime

# Load the OpenAI API key from secrets
api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = api_key

# Set up the page configuration
st.set_page_config(page_title="RFP Navigator", page_icon="🧭")

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help navigate your RFP?"}]
if "history" not in st.session_state:
    st.session_state.history = []
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "log_data" not in st.session_state:
    st.session_state.log_data = []

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
def handle_prompt(text, prompt_template):
    combined_text = " ".join(split_text_into_chunks(text))
    prompt = prompt_template.format(combined_text=combined_text)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[get_system_message(), {"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.1  # Lowered temperature for precise and document-specific responses
        )
        result = response['choices'][0]['message']['content'].strip()
        
        # Log the query and response
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": result
        }
        st.session_state.log_data.append(log_entry)

        return result
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "An error occurred while processing the request."

# Function to save log data to a JSON file
def save_log_data():
    log_file = "rfp_navigator_logs.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            data = json.load(file)
    else:
        data = []

    data.extend(st.session_state.log_data)

    with open(log_file, "w") as file:
        json.dump(data, file, indent=4)

    # Clear the session log data after saving
    st.session_state.log_data = []

# Sidebar for OpenAI API key, PDF uploader, and feedback
with st.sidebar:
    st.title("RFP Navigator 🧭")
    st.markdown('---')  # Add horizontal line after the title

    # PDF uploader with single file check
    uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], key="file_uploader")

    if uploaded_file:
        # Clear previous file if a new one is uploaded
        if st.session_state.uploaded_file and st.session_state.uploaded_file.name != uploaded_file.name:
            st.session_state.extracted_text = ""
            st.session_state.messages = [{"role": "assistant", "content": "How can I help navigate your RFP?"}]
        
        st.session_state.uploaded_file = uploaded_file

        # Extract text from the PDF and store it in session state
        st.session_state.extracted_text = extract_text_from_pdf(uploaded_file.read())

        # Log the PDF upload event
        st.session_state.log_data.append({
            "timestamp": datetime.now().isoformat(),
            "event": "PDF uploaded",
            "file_name": uploaded_file.name
        })

        # Title for the key actions
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

            summary = handle_prompt(st.session_state.extracted_text, summary_template)
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
            crm_data = handle_prompt(st.session_state.extracted_text, crm_data_template)
            st.session_state.messages.append({"role": "assistant", "content": crm_data})

        # Feedback section at the bottom
        st.markdown('---')
        st.subheader("Was this helpful?")
        rating = st.radio("Rate the helpfulness:", options=[1, 2, 3, 4, 5], index=None, horizontal=True, key="feedback_rating")
        comment = st.text_area("Additional comments", placeholder="Enter your feedback here...", key="feedback_comment")

        if st.button("Submit Feedback"):
            feedback_entry = {"rating": rating, "comment": comment}
            st.session_state.feedback.append(feedback_entry)
            st.success("Thank you for your feedback!")

        # Save log data when the session ends
        save_log_data()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
if prompt := st.chat_input("Search your RFP"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from OpenAI
    response = handle_prompt(st.session_state.extracted_text, f"Based on the RFP document text provided below, please answer the following query: {prompt}\n\nRFP Document Text:\n{{combined_text}}")
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)

    # Save log data when a query is made
    save_log_data()
