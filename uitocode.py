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

# Function to generate HTML and CSS in smaller chunks
def generate_html_in_steps(refined_description, temp_image_path):
    # Generate base HTML first
    html_prompt = (
        f"Create an HTML file based on the following UI description, using Bootstrap CSS within the HTML file to style the elements. "
        f"The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. "
        f"Do not include any explanations or comments. Avoid using ```html. Here is the refined description: {refined_description}"
    )
    html_content = send_message_to_model(html_prompt, temp_image_path)

    # Focus on CSS for gradients in a separate step
    css_prompt = (
        f"Now, create the CSS needed to accurately represent the gradients, shadows, borders, and fonts used in the following HTML. "
        f"Ensure that all visual details match the original UI closely. "
        f"Avoid using ```css. Here is the HTML code: {html_content}"
    )
    css_content = send_message_to_model(css_prompt, temp_image_path)

    return html_content, css_content

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

            # Generate UI description
            if st.button("Code UI"):
                st.write("🧑‍💻 Looking at your UI...")
                prompt = (
                    "Describe this UI in accurate details, ensuring that all design elements such as gradients, borders, shadows, and fonts are captured. "
                    "When you reference a UI element, put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. "
                    "Also, describe the color of the elements."
                )
                description = send_message_to_model(prompt, temp_image_path)
                st.write(description)

                # Refine the description
                st.write("🔍 Refining description with visual comparison...")
                refine_prompt = (
                    f"Compare the described UI elements with the provided image and identify any missing elements or inaccuracies. "
                    f"Ensure all gradients, borders, shadows, and fonts are described. "
                    f"Provide a refined and accurate description of the UI elements based on this comparison. "
                    f"Here is the initial description: {description}"
                )
                refined_description = send_message_to_model(refine_prompt, temp_image_path)
                st.write(refined_description)

                # Generate HTML and CSS separately with emphasis on gradients
                html_content, css_content = generate_html_in_steps(refined_description, temp_image_path)

                # Store the generated content in session state
                st.session_state['html_content'] = html_content
                st.session_state['css_content'] = css_content

                st.code(html_content, language='html')
                if css_content:
                    st.code(css_content, language='css')

                st.success("HTML and CSS files have been created.")

            # Provide download links for HTML and CSS if they exist in session state
            if 'html_content' in st.session_state:
                st.download_button(label="Download HTML", data=st.session_state['html_content'], file_name="index.html", mime="text/html")
            if 'css_content' in st.session_state:
                st.download_button(label="Download CSS", data=st.session_state['css_content'], file_name="styles.css", mime="text/css")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
