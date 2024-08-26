import streamlit as st
import base64
from openai import OpenAI
import os

# Set up the OpenAI API key from Streamlit secrets
os.environ['OPENAI_API_KEY'] = st.secrets["openai_api_key"]

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

st.title("Website Builder")

# Upload an image file
upload_file = st.file_uploader("Upload a file", type=["png", "jpg", "jpeg"])
if upload_file:
    with st.expander("Image", expanded=True):
        st.image(upload_file, caption="Uploaded Image")

analyze_button = st.button("Analyze", type="primary")

def chunk_string(string, chunk_size):
    return [string[i:i + chunk_size] for i in range(0, len(string), chunk_size)]

if upload_file is not None and analyze_button:
    with st.spinner("Analyzing..."):
        base64_bytes = base64.b64encode(upload_file.getvalue())
        base64_string = base64_bytes.decode('utf-8')
        
        # Define a smaller chunk size to stay well below the limit
        max_chunk_size = 500 * 1024  # 500 KB per chunk
        chunks = chunk_string(base64_string, max_chunk_size)

        combined_result = ""

        for i, chunk in enumerate(chunks):
            prompt = f"""You are a frontend developer capable of analyzing the given image (encoded below in base64). 
            After analysis, create HTML and CSS code for the website that matches the given image as closely as possible. 
            If needed, you may also write a Python script to load the HTML and CSS code for checking similarity.

            Base64 image data (part {i+1}/{len(chunks)}):
            {chunk}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2048,  # Adjust max tokens for chunk size
                temperature=1,
                top_p=0.95
            )

            combined_result += response.choices[0].message['content']

        st.write(combined_result)
