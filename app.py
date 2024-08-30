# Button to generate pipeline data
if st.button("Generate Pipeline Data"):
    try:
        pipeline_template = """
        Extract and present the following key data points from this RFP document in a table format for CRM entry:
        [pipeline data fields...]
        
        RFP Document Text:
        {extracted_text}
        """

        # Generate response using OpenAI's new SDK method
        response = openai.Client().chat.completions.create(
            model="gpt-4o-mini",  # Use a model you have access to
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": pipeline_template.format(extracted_text=st.session_state.extracted_text)}
            ],
            max_tokens=1024,
            temperature=0.2,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        response_content = response.choices[0].message.content.strip()

        # Append response to the chat history
        st.session_state.messages.append({"role": "assistant", "content": response_content})

        # Log the action to Google Sheets
        log_to_google_sheets(st.session_state.email, uploaded_file.name, "Generate Pipeline Data", response_content)

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
                        log_to_google_sheets(st.session_state.email, uploaded_file.name, message["content"], "Thumbs Up")
                with col2:
                    if st.button("👎", key=f"thumbs_down_{i}", help="Was this Helpful?"):
                        st.session_state.feedback[message['content']] = "Thumbs Down"
                        log_to_google_sheets(st.session_state.email, uploaded_file.name, message["content"], "Thumbs Down")

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

            Document Text:
            {st.session_state.extracted_text}
            """
            response = openai.Client().chat.completions.create(
                model="gpt-4o-mini",  # Use a model you have access to
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query_template}
                ],
                max_tokens=300,  # Adjust this value as needed between 150-300
                temperature=0.2,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )

            response_content = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            with st.chat_message("assistant"):
                st.write(response_content)

            # Log the interaction to Google Sheets
            log_to_google_sheets(st.session_state.email, uploaded_file.name, prompt, response_content)

            # Add thumbs-up and thumbs-down buttons for the response
            col1, col2 = st.columns([0.08, 1])
            with col1:
                if st.button("👍", key=f"thumbs_up_{len(st.session_state.messages)}", help="Was this Helpful?"):
                    st.session_state.feedback[response_content] = "Thumbs Up"
                    log_to_google_sheets(st.session_state.email, uploaded_file.name, response_content, "Thumbs Up")
            with col2:
                if st.button("👎", key=f"thumbs_down_{len(st.session_state.messages)}", help="Was this Helpful?"):
                    st.session_state.feedback[response_content] = "Thumbs Down"
                    log_to_google_sheets(st.session_state.email, uploaded_file.name, response_content, "Thumbs Down")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
