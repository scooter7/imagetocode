import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai

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

            # Generate UI description
            if st.button("Code UI"):
                st.write("🧑‍💻 Looking at your UI...")
                prompt = "Describe this UI in accurate details. When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. Also Describe the color of the elements."
                description = send_message_to_model(prompt, temp_image_path)
                st.session_state['description'] = description
                st.write(description)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    if 'description' in st.session_state:
        description = st.session_state['description']
        if st.button("Refine Description"):
            try:
                st.write("🔍 Refining description with visual comparison...")
                refine_prompt = f"Compare the described UI elements with the provided image and identify any missing elements or inaccuracies. Also Describe the color of the elements. Provide a refined and accurate description of the UI elements based on this comparison. Here is the initial description: {description}"
                refined_description = send_message_to_model(refine_prompt, temp_image_path)
                st.session_state['refined_description'] = refined_description
                st.write(refined_description)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if 'refined_description' in st.session_state:
        refined_description = st.session_state['refined_description']
        if st.button("Generate HTML & CSS"):
            try:
                st.write("🛠️ Generating website...")
                html_prompt = f"Create an HTML file based on the following UI description, using the UI elements described in the previous response. Include {framework} CSS within a separate CSS file to style the elements. Make sure the colors used are the same as the original UI. The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. Here is the refined description: {refined_description}"
                initial_html = send_message_to_model(html_prompt, temp_image_path)
                st.session_state['initial_html'] = initial_html

                if "<style>" in initial_html and "</style>" in initial_html:
                    html_code, css_code = initial_html.split("<style>", 1)
                    css_code = css_code.replace("</style>", "")
                else:
                    html_code = initial_html
                    css_code = "/* No CSS found in the model's response */"

                st.code(html_code, language='html')
                st.code(css_code, language='css')

                # Save the HTML and CSS to files
                with open("index.html", "w") as file:
                    file.write(html_code)
                with open("style.css", "w") as file:
                    file.write(css_code)

                st.success("HTML file 'index.html' and CSS file 'style.css' have been created.")

                # Provide download link for HTML and CSS
                st.download_button(label="Download HTML", data=html_code, file_name="index.html", mime="text/html")
                st.download_button(label="Download CSS", data=css_code, file_name="style.css", mime="text/css")
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
