import openai
import fitz  # PyMuPDF
import streamlit as st

# Load the OpenAI API key from secrets
api_key = st.secrets["openai"]["OPENAI_API_KEY"]

# Use the API key
openai.api_key = api_key

st.title("RFP Navigator 🧭")

# Step 1: Upload PDF and Extract Text
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    try:
        # Extract text from the uploaded PDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Display the extracted text for now (optional, for debugging)
        st.text_area("Extracted Text", value=text, height=300)

        # Step 2: Interact with OpenAI API
        if st.button("Process with OpenAI"):
            # Sample prompt template
            prompt = f"Please analyze the following RFP document text:\n\n{text[:1500]}"

            # Call OpenAI API
            response = openai.Completion.create(
                model="gpt-3.5-turbo",
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5
            )

            # Display the OpenAI response
            st.write("Response from OpenAI:")
            st.write(response.choices[0].text.strip())

    except Exception as e:
        st.error(f"Error: {e}")
