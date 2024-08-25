import openai
import fitz  # PyMuPDF
import streamlit as st

# Debugging Step 1: Check if st.secrets has any content at all
st.write("Debug Step 1: st.secrets content:", st.secrets)

# Debugging Step 2: Attempt to retrieve the OpenAI API key using the correct key name
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.write("Debug Step 2: Successfully retrieved API key.")  # Debugging
except KeyError as e:
    st.error(f"Debug Step 2: Failed to retrieve API key. KeyError: {e}")

# Debugging Step 3: Set the API key for OpenAI and verify
try:
    openai.api_key = api_key
    st.write("Debug Step 3: Successfully set OpenAI API key.")  # Debugging
except Exception as e:
    st.error(f"Debug Step 3: Failed to set OpenAI API key. Error: {e}")

# Debugging Step 4: Check if the OpenAI API key is correctly set
st.write(f"Debug Step 4: OpenAI API Key: {api_key}")

st.title("RFP Navigator")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    try:
        # Extract text from the uploaded PDF
        st.write("Debug Step 5: Uploading PDF...")  # Debugging
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Display the extracted text
        st.text_area("Extracted Text", value=text, height=300)

        # Prepare a simple prompt template
        prompt_template = """
        Based on the following text from an RFP document, please summarize the key points:

        RFP Document Text:
        {extracted_text}
        """

        # Handle the prompt and get the response from OpenAI
        if st.button("Generate Summary"):
            st.write("Debug Step 6: Generating summary...")  # Debugging
            prompt = prompt_template.format(extracted_text=text)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5
            )
            st.text_area("Summary", value=response.choices[0].text.strip(), height=300)
    except Exception as e:
        st.error(f"Debug Step 7: Error processing PDF or generating summary. Error: {e}")
