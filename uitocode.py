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

# Function to send a message to the model
def send_message_to_model(message, image_path=None):
    if image_path:
        image_input = {
            'mime_type': 'image/jpeg',
            'data': pathlib.Path(image_path).read_bytes()
        }
        response = chat_session.send_message([message, image_input])
    else:
        response = chat_session.send_message([message])
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

            # Generate robust UI analysis
            if st.button("Analyze UI"):
                st.write("🔍 Analyzing your UI in detail...")
                prompt = (
                    "Analyze the attached UI image thoroughly. "
                    "Provide a comprehensive breakdown of the UI, including: "
                    "1. A detailed description of the layout structure, including headers, footers, main sections, and any sidebars. "
                    "2. Identification and description of all UI components (e.g., buttons, text fields, images) with their bounding boxes in the format: [object name (y_min, x_min, y_max, x_max)]. "
                    "3. A detailed description of the color scheme used, including specific colors and gradients, with exact color codes where possible. "
                    "4. An explanation of any typography used, including font families, sizes, and styles. "
                    "5. An assessment of the spacing, padding, and margin strategies used throughout the UI. "
                    "6. A breakdown of any interactive elements (e.g., hover effects, animations) and their expected behaviors. "
                    "7. Recommendations for best practices or potential improvements based on the analysis."
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
                st.write("🛠️ Generating HTML...")
                html_prompt = (
                    f"Generate only the HTML code for the following UI. "
                    f"Do not include any explanations, comments, or non-HTML content. "
                    f"Use Bootstrap for layout and structure. "
                    f"Here is the description: {description}"
                )
                html_code = send_message_to_model(html_prompt)
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
                    f"Generate only the CSS code to style the HTML structure. "
                    f"Do not include any explanations, comments, or non-CSS content. "
                    f"Ensure that colors, gradients, padding, margins, fonts, and other styling elements are properly defined."
                )
                css_code = send_message_to_model(css_prompt)
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
                revised_html_bytes = revised_html_css.encode('utf-8')
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
