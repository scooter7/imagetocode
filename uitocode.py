import streamlit as st
import pathlib
from PIL import Image
import openai
import time

# Configure the API key from Streamlit secrets
openai.api_key = st.secrets["openai_api_key"]

# Function to send a message to the model
def send_message_to_model(prompt, image_path):
    image_data = pathlib.Path(image_path).read_bytes()
    retries = 3
    for attempt in range(retries):
        try:
            # Simplified image description
            image_description = "Image data: " + str(image_data[:100])  # Simplified image description
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"{prompt}\n{image_description}"}
                ],
                max_tokens=8192,
                n=1,
                stop=None,
                temperature=1,
                top_p=0.95
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            if '429' in str(e):
                st.error("Rate limit exceeded. Retrying in 60 seconds...")
                time.sleep(60)
            else:
                st.error(f"An error occurred: {e}")
                return None
    st.error("Failed to get a response after several attempts.")
    return None

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
                prompt = "Describe this UI in accurate details. When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. Also describe the color of the elements."
                description = send_message_to_model(prompt, temp_image_path)
                if description:
                    st.write(description)

                    # Refine the description
                    st.write("🔍 Refining description with visual comparison...")
                    refine_prompt = f"Compare the described UI elements with the provided image and identify any missing elements or inaccuracies. Also describe the color of the elements. Provide a refined and accurate description of the UI elements based on this comparison. Here is the initial description: {description}"
                    refined_description = send_message_to_model(refine_prompt, temp_image_path)
                    if refined_description:
                        st.write(refined_description)

                        # Generate HTML
                        st.write("🛠️ Generating website...")
                        html_prompt = f"Create an HTML file based on the following UI description, using the UI elements described in the previous response. Include {framework} CSS within the HTML file to style the elements. Make sure the colors used are the same as the original UI. The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. Do not include any explanations or comments. Avoid using ```html. and ``` at the end. ONLY return the HTML code with inline CSS. Here is the refined description: {refined_description}"
                        initial_html = send_message_to_model(html_prompt, temp_image_path)
                        if initial_html:
                            st.code(initial_html, language='html')

                            # Refine HTML
                            st.write("🔧 Refining website...")
                            refine_html_prompt = f"Validate the following HTML code based on the UI description and image and provide a refined version of the HTML code with {framework} CSS that improves accuracy, responsiveness, and adherence to the original design. ONLY return the refined HTML code with inline CSS. Avoid using ```html. and ``` at the end. Here is the initial HTML: {initial_html}"
                            refined_html = send_message_to_model(refine_html_prompt, temp_image_path)
                            if refined_html:
                                st.code(refined_html, language='html')

                                # Save the refined HTML to a file
                                with open("index.html", "w") as file:
                                    file.write(refined_html)
                                st.success("HTML file 'index.html' has been created.")

                                # Provide download link for HTML
                                st.download_button(label="Download HTML", data=refined_html, file_name="index.html", mime="text/html")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
