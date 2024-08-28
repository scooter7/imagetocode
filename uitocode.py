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
    "max_output_tokens": 8192,
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

# Function to send a message to the model with chunking strategy
def send_message_to_model(message, image_path):
    image_input = {
        'mime_type': 'image/jpeg',
        'data': pathlib.Path(image_path).read_bytes()
    }
    response = chat_session.send_message([message, image_input])

    # Implement chunking if the response is too large
    if len(response.text) > 8000:
        chunks = [response.text[i:i+8000] for i in range(0, len(response.text), 8000)]
        return ''.join(chunks)
    
    return response.text

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
                prompt = "Describe this UI in accurate details. When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. Also Describe the color of the elements."
                description = send_message_to_model(prompt, temp_image_path)
                st.write(description)

                # Refine the description
                st.write("🔍 Refining description with visual comparison...")
                refine_prompt = f"Compare the described UI elements with the provided image and identify any missing elements or inaccuracies. Also Describe the color of the elements. Provide a refined and accurate description of the UI elements based on this comparison. Here is the initial description: {description}"
                refined_description = send_message_to_model(refine_prompt, temp_image_path)
                st.write(refined_description)

                # Generate HTML and CSS
                st.write("🛠️ Generating website...")
                html_prompt = f"Create separate HTML and CSS files based on the following UI description, using the UI elements described in the previous response. Include Bootstrap CSS within the CSS file to style the elements. Make sure the colors used are the same as the original UI. The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. Do not include any explanations or comments. Avoid using ```html or ```css. Here is the refined description: {refined_description}"
                initial_html = send_message_to_model(html_prompt, temp_image_path)
                
                # Separate HTML and CSS content
                html_content, css_content = initial_html.split('<style>')[0], initial_html.split('<style>')[1].replace('</style>', '')

                st.code(html_content, language='html')
                st.code(css_content, language='css')

                # Save the HTML and CSS to separate files
                with open("index.html", "w") as html_file:
                    html_file.write(html_content)
                with open("styles.css", "w") as css_file:
                    css_file.write(css_content)
                
                st.success("HTML and CSS files have been created.")

                # Provide download links for HTML and CSS
                st.download_button(label="Download HTML", data=html_content, file_name="index.html", mime="text/html")
                st.download_button(label="Download CSS", data=css_content, file_name="styles.css", mime="text/css")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
