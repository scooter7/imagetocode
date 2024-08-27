import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai
import zipfile
import io

# Configure the API key from Streamlit secrets
API_KEY = st.secrets["gemini_api_key"]
genai.configure(api_key=API_KEY)

# Generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
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

# Framework selection
framework = "Bootstrap"

# Create the model
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings,
    generation_config=generation_config,
)

# Start a chat session
chat_session = model.start_chat(history=[])

# Function to send a message to the model with chunking and retry mechanism
def send_message_to_model(message, image_path, chunk_size=1024):
    image_input = {
        'mime_type': 'image/jpeg',
        'data': pathlib.Path(image_path).read_bytes()
    }
    
    chunks = [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]
    responses = []
    
    for chunk in chunks:
        try:
            response = chat_session.send_message([chunk, image_input])
            responses.append(response.text)
        except Exception as e:
            if 'RECITATION' in str(e):
                st.warning("Recitation error occurred. Retrying with smaller chunk size...")
                return send_message_to_model(message, image_path, chunk_size // 2)
            else:
                raise e
    
    return "".join(responses)

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

            # Step 1: Initial Description and Analysis
            if st.button("Analyze UI"):
                st.write("🔍 Analyzing the UI elements...")
                analysis_prompt = (
                    "Analyze the attached UI image. Provide a detailed description of the colors used, gradients, div structure, "
                    "font styles, and any other relevant design elements. Focus on elements that will be important for generating HTML and CSS. "
                    "This analysis will guide the generation of the HTML structure and CSS styling."
                )
                analysis_description = send_message_to_model(analysis_prompt, temp_image_path)
                st.session_state['analysis_description'] = analysis_description

                st.write(analysis_description)

            # Step 2: Generate HTML
            if 'analysis_description' in st.session_state and st.button("Generate HTML"):
                st.write("🛠️ Generating HTML based on analysis...")
                html_prompt = (
                    "Based on the following analysis of the UI elements, generate the HTML code for the webpage. "
                    "Use appropriate HTML5 semantic elements such as <header>, <section>, <nav>, <article>, and <footer>. "
                    "Ensure that the layout is responsive and uses the Bootstrap grid system with proper class names. "
                    "Return only valid HTML code without any descriptions or explanations. "
                    "Here is the analysis: {analysis_description}".format(analysis_description=st.session_state['analysis_description'])
                )
                html_code = send_message_to_model(html_prompt, temp_image_path)
                st.session_state['html_code'] = html_code

                st.code(html_code, language='html')

            # Step 3: Generate CSS
            if 'html_code' in st.session_state and st.button("Generate CSS"):
                st.write("🎨 Generating CSS based on analysis...")
                css_prompt = (
                    "Based on the following analysis of the UI elements, generate the CSS code to style the HTML structure. "
                    "Ensure that the colors, gradients, padding, margins, and font styles match the design elements described. "
                    "Ensure the CSS adheres to responsive design principles. Return only valid CSS code. "
                    "Here is the analysis: {analysis_description}".format(analysis_description=st.session_state['analysis_description'])
                )
                css_code = send_message_to_model(css_prompt, temp_image_path)
                st.session_state['css_code'] = css_code

                st.code(css_code, language='css')

                # Save the HTML and CSS to files in-memory
                html_bytes = st.session_state['html_code'].encode('utf-8')
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

if __name__ == "__main__":
    main()
