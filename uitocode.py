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
    "temperature": 0.7,  # Reduced temperature to focus on more predictable outputs
    "top_p": 0.9,        # Reduced top_p to limit diversity
    "top_k": 40,         # Reduced top_k to limit the range of outputs
    "max_output_tokens": 4096,  # Reduced max_output_tokens to avoid exceeding limits
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

# Function to send a message to the model
def send_message_to_model(message, image_path):
    image_input = {
        'mime_type': 'image/jpeg',
        'data': pathlib.Path(image_path).read_bytes()
    }
    response = chat_session.send_message([message, image_input])
    return response.text

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

            # Generate UI description
            if st.button("Code UI"):
                st.write("🧑‍💻 Looking at your UI...")
                prompt = "Describe this UI with essential details only, focusing on layout, main elements, colors, and gradients."
                description = send_message_to_model(prompt, temp_image_path)
                st.session_state['description'] = description
                st.write(description)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    if 'description' in st.session_state:
        description = st.session_state['description']
        if st.button("Generate HTML"):
            try:
                st.write("🛠️ Generating HTML...")
                html_prompt = (
                    f"Create the HTML structure based on the following UI description. "
                    f"Focus on key elements, layout, and responsiveness using {framework}. "
                    f"Avoid generating unnecessary details. "
                    f"Here is the description: {description}"
                )
                html_code = send_message_to_model(html_prompt, temp_image_path)
                st.session_state['html_code'] = html_code
                st.code(html_code, language='html')

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if 'html_code' in st.session_state:
        html_code = st.session_state['html_code']
        if st.button("Generate CSS"):
            try:
                st.write("🎨 Generating CSS...")
                css_prompt = (
                    f"Generate the CSS code to style the HTML structure. "
                    f"Ensure colors, gradients, padding, margins, fonts, and other styling elements are properly defined. "
                    f"Use {framework} for responsiveness."
                )
                css_code = send_message_to_model(css_prompt, temp_image_path)
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

if __name__ == "__main__":
    main()
