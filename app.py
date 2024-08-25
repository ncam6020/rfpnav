import openai
import fitz  # PyMuPDF
import streamlit as st

# Set up the OpenAI API key
api_key = st.secrets["openai_api_key"]
openai.api_key = api_key

st.write(f"OpenAI API Key: {api_key}")  # Debugging: check if the key is being retrieved correctly

st.title("RFP Navigator")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    try:
        # Extract text from the uploaded PDF
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
            prompt = prompt_template.format(extracted_text=text)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5
            )
            st.text_area("Summary", value=response.choices[0].text.strip(), height=300)
    except Exception as e:
        st.error(f"Error: {e}")
