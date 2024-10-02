import streamlit as st
import generator
st.title("Gemini Powered Large Document Summarizer")


user_input_url = st.text_input("Enter URL", "https://services.google.com/fh/files/misc/practitioners_guide_to_mlops_whitepaper.pdf")


if st.button('Generate Summary'):
    status=st.info("Generation started")
    result = generator.start_generation(user_input_url)
    print(type(result))
    if type(result) is str:
        status.empty()
        st.info("Generation Completed")
        st.write(result)


