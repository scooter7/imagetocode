import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai
import zipfile
import io
import re
from bs4 import BeautifulSoup
import cssutils

# Configure the API key from Streamlit secrets
API_KEY = st.secrets["gemini_api_key"]
genai.configure(api_key=API_KEY)

# Generation configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 4096,
    "response_mime_type": "text/plain",
}

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Model name
MODEL_NAME = "gemini-1.5-pro-latest"

# Framework selection (e.g., Tailwind, Bootstrap, etc.)
framework = "Bootstrap"

# Create the model
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings,
    generation_config=generation_config,
)

# Start a chat session
chat_session = model.start_chat(history=[])

# Function to send a message to the model with dynamic chunking strategy
def send_message_to_model(message, image_path=None, chunk_size=1024):
    image_input = None
    if image_path:
        image_input = {
            'mime_type': 'image/jpeg',
            'data': pathlib.Path(image_path).read_bytes()
        }

    # Split the message into chunks
    chunks = [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]
    responses = []
    
    for chunk in chunks:
        try:
            if image_input:
                response = chat_session.send_message([chunk, image_input])
            else:
                response = chat_session.send_message([chunk])
            responses.append(response.text)
        except Exception as e:
            if 'RECITATION' in str(e):
                if chunk_size > 512:
                    st.warning(f"Recitation error occurred. Retrying with smaller chunk size: {chunk_size // 2}...")
                    return send_message_to_model(message, image_path, chunk_size // 2)
                else:
                    st.error("Recitation error occurred even with the smallest chunk size. Please simplify your request.")
                    return ""
            else:
                raise e
    
    return "".join(responses)

# Enhanced cleaning function
def clean_code(code):
    code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'[^{}<>:;\.\#\-\w\s\n\(\)\[\]\=\"]+', '', code)
    code = re.sub(r'\s+', ' ', code).strip()
    return code

# HTML validation and formatting
def validate_and_format_html(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    formatted_html = soup.prettify()
    return formatted_html

# CSS validation and formatting
def validate_and_format_css(css_code):
    parser = cssutils.CSSParser(raiseExceptions=True)
    sheet = parser.parseString(css_code)
    return sheet.cssText.decode('utf-8')

# Integration with your app
def main():
    st.title("UI to Code 👨‍💻 ")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image.', use_column_width=True)

            if image.mode == 'RGBA':
                image = image.convert('RGB')

            temp_image_path = pathlib.Path("temp_image.jpg")
            image.save(temp_image_path, format="JPEG")

            if st.button("Analyze UI"):
                st.write("🔍 Analyzing your UI in detail...")
                prompt = (
                    "Analyze the attached UI image thoroughly. "
                    "Provide a detailed description of the div structure, UI components, colors, typography, spacing, gradients, and HTML elements. "
                    "Do not include any qualitative analysis or best practice recommendations."
                )
                description = send_message_to_model(prompt, temp_image_path)
                st.session_state['description'] = description
                st.write(description)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    if 'description' in st.session_state:
        description = st.session_state['description']
        if st.button("Generate HTML"):
            try:
                st.write("🛠️ Generating detailed HTML...")
                html_code = generate_html_from_analysis(description)
                html_code = clean_code(html_code)
                html_code = validate_and_format_html(html_code)
                st.session_state['html_code'] = html_code
                st.code(html_code, language='html')

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if 'html_code' in st.session_state:
        html_code = st.session_state['html_code']
        if st.button("Generate CSS"):
            try:
                css_code = generate_css_from_html(html_code)
                css_code = clean_code(css_code)
                css_code = validate_and_format_css(css_code)
                st.session_state['css_code'] = css_code
                st.code(css_code, language='css')

                html_bytes = html_code.encode('utf-8')
                css_bytes = css_code.encode('utf-8')
                in_memory_zip = io.BytesIO()
                with zipfile.ZipFile(in_memory_zip, "w") as zf:
                    zf.writestr("index.html", html_bytes)
                    zf.writestr("style.css", css_bytes)
                in_memory_zip.seek(0)

                st.success("HTML and CSS files have been created.")

                st.download_button(label="Download ZIP", data=in_memory_zip, file_name="web_files.zip", mime="application/zip")

            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Optional Revision Step remains the same

if __name__ == "__main__":
    main()
