import openai
import fitz  # PyMuPDF
import streamlit as st

# Load the OpenAI API key from secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Use the API key
openai.api_key = api_key

# Set up the page configuration
st.set_page_config(page_title="RFP Navigator", page_icon="🧭")

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help navigate your RFP?"}]

if "history" not in st.session_state:
    st.session_state["history"] = []

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

# General function to handle any prompt
def handle_prompt(text, prompt_template):
    combined_text = " ".join(split_text_into_chunks(text, chunk_size=1500))
    prompt = prompt_template.format(combined_text=combined_text)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Enable executives at Perkins&Will to swiftly and accurately analyze RFP documents, highlighting crucial information needed for go/no-go decisions and facilitating the initial steps of proposal development."},
                  {"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.5
    )
    return response['choices'][0]['message']['content'].strip()

# Sidebar for OpenAI API key, PDF uploader, and feedback
with st.sidebar:
    st.title("RFP Navigator 🧭")
    st.markdown('---')  # Add horizontal line after the title
    uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], key="file_uploader")

    if uploaded_file:
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(uploaded_file.read())

        # Title for the key actions
        st.markdown('---')
        st.subheader("**Key Actions**")

        if st.button("Generate Executive Summary"):
            action_text = "Generate Executive Summary"
            st.session_state.messages.append({"role": "user", "content": action_text})
            summary_template = """
            Please create a one-page executive summary of this RFP document, including key dates (issue date, response due date, and selection date), a project overview, the scope of work, and a list of deliverables. Ensure the summary is concise but captures all necessary details for a quick review.

            RFP Document Text:
            {combined_text}
            """
            summary = handle_prompt(extracted_text, summary_template)
            st.session_state.messages.append({"role": "assistant", "content": summary})

        if st.button("Gather Data"):
            action_text = "Gather Data"
            st.session_state.messages.append({"role": "user", "content": action_text})
            crm_data_template = """
            Extract and present the following key data points from this RFP document in a table format for CRM entry:
            - RFP Issue Date
            - RFP Response Due Date
            - Primary Contact (name, title, email, and phone)
            - Secondary Contact
            - Project Name
            - Locations
            - Scope of Services
            - Project Schedule Milestones
            - Minimum Qualifications
            - Evaluation Criteria
            - Preproposal Conference
            - Submission Requirements
            - Key Strategic Goals
            - CRM Tagging
            - Additional Information

            RFP Document Text:
            {combined_text}
            """
            crm_data = handle_prompt(extracted_text, crm_data_template)
            st.session_state.messages.append({"role": "assistant", "content": crm_data})

        # Feedback section at the bottom
        st.markdown('---')
        st.subheader("Was this helpful?")
        rating = st.radio("Rate the helpfulness:", options=[1, 2, 3, 4, 5], index=None, horizontal=True, key="feedback_rating")
        comment = st.text_area("Additional comments", placeholder="Enter your feedback here...", key="feedback_comment")

        if st.button("Submit Feedback"):
            st.write("Thank you for your feedback!")
            st.write(f"Rating: {rating}")
            st.write(f"Comment: {comment}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
if prompt := st.chat_input("Search the RFP:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from OpenAI
    response = handle_prompt(extracted_text, f"Based on the RFP document text provided below, please answer the following query: {prompt}\n\nRFP Document Text:\n{{combined_text}}")
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
