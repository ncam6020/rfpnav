import openai
import streamlit as st
import os

# Access OpenAI API key from secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Set the API key for OpenAI
openai.api_key = api_key

# Test the access by displaying the key (just for testing, don't display in production)
st.write("OpenAI API Key:", api_key)

# Use the API key with OpenAI (Example)
response = openai.Completion.create(
    model="text-davinci-003",
    prompt="Say hello!",
    max_tokens=5
)

# Display the response from OpenAI
st.write("OpenAI Response:", response.choices[0].text.strip())
