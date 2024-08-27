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
    "max_output_tokens": 1024,  # Further reduced to manage token limits
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

            # Generate UI description and HTML & CSS in one step
            if st.button("Generate HTML & CSS"):
                st.write("🛠️ Generating UI description, HTML, and CSS...")
                prompt = (
                    "Describe this UI in accurate details. "
                    "When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. "
                    "Also Describe the color of the elements. "
                    "Then, create an HTML file based on this UI description, using Bootstrap CSS within a separate CSS file to style the elements. "
                    "The UI needs to be responsive and mobile-first, matching the original UI as closely as possible."
                )
                initial_html = send_message_to_model(prompt, temp_image_path)
                st.session_state['initial_html'] = initial_html

                if "<style>" in initial_html and "</style>" in initial_html:
                    html_code, css_code = initial_html.split("<style>", 1)
                    css_code = css_code.replace("</style>", "")
                else:
                    html_code = initial_html
                    css_code = "/* No CSS found in the model's response */"

                st.code(html_code, language='html')
                st.code(css_code, language='css')

                # Save the HTML and CSS to files in-memory
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

    if 'initial_html' in st.session_state:
        initial_html = st.session_state['initial_html']
        if st.button("Revise HTML & CSS"):
            try:
                st.write("🔧 Refining HTML & CSS...")
                refine_html_prompt = (
                    "Validate the following HTML code based on the UI description and image and provide a refined version "
                    "of the HTML code with Bootstrap CSS that improves accuracy, responsiveness, and adherence to the original design. "
                    "ONLY return the refined HTML code with inline CSS. Avoid using ```html. and ``` at the end."
                )
                refined_html = send_message_to_model(refine_html_prompt, temp_image_path)
                st.session_state['refined_html'] = refined_html

                if "<style>" in refined_html and "</style>" in refined_html:
                    html_code, css_code = refined_html.split("<style>", 1)
                    css_code = css_code.replace("</style>", "")
                else:
                    html_code = refined_html
                    css_code = "/* No CSS found in the model's response */"

                st.code(html_code, language='html')
                st.code(css_code, language='css')

                # Save the refined HTML and CSS to files in-memory
                html_bytes = html_code.encode('utf-8')
                css_bytes = css_code.encode('utf-8')
                in_memory_zip = io.BytesIO()
                with zipfile.ZipFile(in_memory_zip, "w") as zf:
                    zf.writestr("index.html", html_bytes)
                    zf.writestr("style.css", css_bytes)
                in_memory_zip.seek(0)

                st.success("Refined HTML and CSS files have been created.")

                # Provide download link for the refined zip file
                st.download_button(label="Download Refined ZIP", data=in_memory_zip, file_name="refined_web_files.zip", mime="application/zip")

            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
