import streamlit as st
import fitz  # PyMuPDF

st.title("PDF Text Extraction Test")

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
    except Exception as e:
        st.error(f"Error extracting text: {e}")
