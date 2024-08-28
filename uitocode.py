import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai

# Configure the API key using Streamlit secrets
API_KEY = st.secrets["google_gemini_api_key"]
genai.configure(api_key=API_KEY)

# Generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2048,  # Reduced to avoid recitation issues
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

# Function to send a message to the model
def send_message_to_model(message, image_path):
    image_input = {
        'mime_type': 'image/jpeg',
        'data': pathlib.Path(image_path).read_bytes()
    }

    # Send the message and get the response
    response = chat_session.send_message([message, image_input])
    return response.text

# Function to generate and validate each section independently
def generate_and_validate_section(section_name, image_path, existing_html=""):
    section_prompt = (
        f"Generate the {section_name} section of an HTML page, ensuring it is properly structured with no missing tags. "
        f"Use Bootstrap for styling and ensure that there are no repeated elements. "
        f"Include only the HTML code, and avoid adding any comments or code blocks like ```html. "
        f"Here is the existing HTML content: {existing_html}"
    )
    section_html = send_message_to_model(section_prompt, image_path)
    return section_html

# Streamlit app
def main():
    st.title("Gemini 1.5 Pro, UI to Code 👨‍💻 ")
    st.subheader('Made with ❤️ by [Skirano](https://x.com/skirano)')

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

            # Generate each section independently
            if st.button("Generate HTML"):
                st.write("Generating HTML...")

                # Generate header
                header_html = generate_and_validate_section("header", temp_image_path)
                st.write("Header generated.")

                # Generate main content
                main_content_html = generate_and_validate_section("main content", temp_image_path, existing_html=header_html)
                st.write("Main content generated.")

                # Generate footer
                footer_html = generate_and_validate_section("footer", temp_image_path, existing_html=main_content_html)
                st.write("Footer generated.")

                # Combine all sections
                full_html = header_html + main_content_html + footer_html

                # Store the final HTML in session state
                st.session_state['html_content'] = full_html

                # Generate CSS
                css_prompt = (
                    "Extract all the CSS from the following HTML and generate a single, well-structured CSS file. "
                    "Ensure all styles are included and formatted correctly. "
                    "Return only the CSS code without any comments or code blocks like ```css."
                )
                combined_css = send_message_to_model(css_prompt, temp_image_path)

                # Store the CSS in session state
                st.session_state['css_content'] = combined_css

                st.code(full_html, language='html')
                st.code(combined_css, language='css')

                st.success("HTML and CSS files have been generated successfully!")

            # Provide download links for HTML and CSS if they exist in session state
            if 'html_content' in st.session_state:
                st.download_button(label="Download HTML", data=st.session_state['html_content'], file_name="index.html", mime="text/html")
            if 'css_content' in st.session_state:
                st.download_button(label="Download CSS", data=st.session_state['css_content'], file_name="styles.css", mime="text/css")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
