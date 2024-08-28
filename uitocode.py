import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai
import zipfile
import io
import re

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

# Function to clean up the code by removing comments and non-code content
def clean_code(code):
    # Remove HTML comments
    code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
    # Remove CSS comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code.strip()

# Function to generate HTML for specific UI sections based on the analysis
def generate_html_from_analysis(description):
    sections = [
        "header",
        "footer",
        "main content",
        "sidebar",
        "interactive elements"
    ]
    html_parts = []

    for section in sections:
        st.write(f"Generating HTML for {section}...")
        prompt = (
            f"Generate HTML for the {section} based on the following UI analysis. "
            f"Use semantic HTML5 tags and Bootstrap classes for layout. "
            f"Do not include any comments, explanations, or non-code content. "
            f"UI analysis: {description}"
        )
        html_part = send_message_to_model(prompt)
        clean_html = clean_code(html_part)
        html_parts.append(clean_html)
        st.code(clean_html, language='html')
    
    return "\n".join(html_parts)

# Function to generate CSS for the HTML
def generate_css_from_html(html_code):
    st.write("Generating CSS for the provided HTML...")
    prompt = (
        f"Generate CSS to style the following HTML. "
        f"Include styling for colors, gradients, padding, margins, and fonts. "
        f"Do not include any comments or explanations. "
        f"HTML: {html_code}"
    )
    css_code = send_message_to_model(prompt)
    return clean_code(css_code)

# Streamlit app
def main():
    st.title("UI to Code 👨‍💻 ")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            # Load and display the image
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image.', use_column_width=True)

            # Convert image to RGB mode if it has an alpha channel
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Save the uploaded image temporarily
            temp_image_path = pathlib.Path("temp_image.jpg")
            image.save(temp_image_path, format="JPEG")

            # Generate detailed UI analysis
            if st.button("Analyze UI"):
                st.write("🔍 Analyzing your UI in detail...")
                prompt = (
                    "Analyze the attached UI image thoroughly. "
                    "Provide a detailed description of the layout, UI components, colors, typography, spacing, and interactions."
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
                st.session_state['html_code'] = html_code

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if 'html_code' in st.session_state:
        html_code = st.session_state['html_code']
        if st.button("Generate CSS"):
            try:
                css_code = generate_css_from_html(html_code)
                st.session_state['css_code'] = css_code
                st.code(css_code, language='css')

                # Save HTML and CSS files in memory
                html_bytes = html_code.encode('utf-8')
                css_bytes = css_code.encode('utf-8')
                in_memory_zip = io.BytesIO()
                with zipfile.ZipFile(in_memory_zip, "w") as zf:
                    zf.writestr("index.html", html_bytes)
                    zf.writestr("style.css", css_bytes)
                in_memory_zip.seek(0)

                st.success("HTML and CSS files have been created.")

                # Provide download link for the zip file
                st.download_button(label="Download ZIP", data=in_memory_zip, file_name="web_files.zip", mime="application/zip")

            except Exception as e:
                st.error(f"An error occurred: {e}")

        # Optional Revision Step
        revision_instructions = st.text_area("Enter revision instructions (optional):", "")
        if revision_instructions and st.button("Apply Revision"):
            try:
                st.write("🔧 Applying revision...")
                revision_prompt = (
                    f"Revise the HTML and CSS based on the following instructions: {revision_instructions}. "
                    f"Ensure that the HTML and CSS match the new requirements."
                )
                revised_html_css = send_message_to_model(revision_prompt)
                
                # Save the revised HTML and CSS files in memory
                revised_html_bytes = clean_code(revised_html_css).encode('utf-8')
                in_memory_zip = io.BytesIO()
                with zipfile.ZipFile(in_memory_zip, "w") as zf:
                    zf.writestr("revised_index.html", revised_html_bytes)
                    zf.writestr("revised_style.css", revised_html_bytes)
                in_memory_zip.seek(0)

                st.success("Revised HTML and CSS files have been created.")

                # Provide download link for the revised zip file
                st.download_button(label="Download Revised ZIP", data=in_memory_zip, file_name="revised_web_files.zip", mime="application/zip")

            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
