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
    "max_output_tokens": 2048,
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

# Function to analyze the image and generate a description of the UI components
def analyze_image_and_generate_description(image_path):
    prompt = (
        "Analyze the provided image and generate a detailed description of all UI components. "
        "Ensure to include all sections like headers, footers, navigation bars, sidebars, buttons, forms, and any other significant elements. "
        "For each component, describe its layout, color, text, and any interactive elements. "
        "Provide this information in a format that can be used to generate clean and structured HTML and CSS code."
    )
    description = send_message_to_model(prompt, image_path)
    return description

# Function to generate the full HTML document
def generate_full_html(description):
    prompt = (
        "Based on the following description, generate a full HTML5 document. "
        "Ensure the document includes a DOCTYPE declaration, and proper opening and closing tags for <html>, <head>, and <body>. "
        "The HTML should be well-structured, clean, and ready for use: "
        f"{description}"
    )
    full_html = send_message_to_model(prompt)
    return full_html

# Function to generate CSS for the entire page
def generate_css_for_page(full_html):
    prompt = (
        "Extract and generate the CSS for the following HTML. "
        "Ensure all styles are correctly applied and formatted. "
        "Do not include any comments or code blocks like ```css. "
        "Return only the valid CSS code."
    )
    css_content = send_message_to_model(prompt)
    return css_content

# Streamlit app
def main():
    st.title("Gemini 1.5 Pro, UI to Code 👨‍💻")
    st.subheader('Made with ❤️ by [Skirano](https://x.com/skirano)')

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            # Load and display the image
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image.', use_column_width=True)

            # Convert the image to RGB mode if it has an alpha channel (RGBA)
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Save the uploaded image temporarily
            temp_image_path = pathlib.Path("temp_image.jpg")
            image.save(temp_image_path, format="JPEG")

            if st.button("Generate HTML and CSS"):
                st.write("Analyzing image and generating UI description...")
                description = analyze_image_and_generate_description(temp_image_path)
                st.write(description)

                st.write("Generating full HTML document...")
                full_html = generate_full_html(description)

                st.write("Generating CSS...")
                combined_css = generate_css_for_page(full_html)

                # Store the generated content in session state
                st.session_state['html_content'] = full_html
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
