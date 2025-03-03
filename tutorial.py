import streamlit as st
import webbrowser
from PIL import Image
import requests
from io import BytesIO
import hashlib
import importlib.util
import sys
import os

# Function to dynamically import the base_urls from the uploaded .py file
def import_base_urls_from_file(file_path):
    module_name = "uploaded_base_urls"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.IMAGE_BASE_URLS, module.VIDEO_BASE_URLS

# Function to fetch and display images
def display_images(image_data):
    # Sort sections alphabetically
    sorted_sections = sorted(image_data.keys())
    
    for section in sorted_sections:
        st.write(f"### Section: {section} (Total Images: {len(image_data[section])})")
        cols = st.columns(4)  # Display 4 images per row
        for idx, (name, url) in enumerate(image_data[section]):
            try:
                response = requests.get(url, timeout=10)  # Add timeout for requests
                response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
                image = Image.open(BytesIO(response.content))
                with cols[idx % 4]:  # Cycle through columns
                    st.image(image, caption=f"{section}{idx + 1:03}", use_container_width=True)
                    # Use st.markdown to create a link that opens in a new tab
                    st.markdown(f'<a href="{url}" target="_blank">Open {section}{idx + 1:03}</a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to load image from {url}: {e}")

# Function to display videos
def display_videos(video_data):
    # Sort sections alphabetically
    sorted_sections = sorted(video_data.keys())
    
    for section in sorted_sections:
        st.write(f"### Section: {section} (Total Videos: {len(video_data[section])})")
        cols = st.columns(4)  # Display 4 videos per row
        for idx, (name, url) in enumerate(video_data[section]):
            with cols[idx % 4]:  # Cycle through columns
                # Display a placeholder for the video
                st.write(f"🎥 {section}{idx + 1:03}")
                # Use st.markdown to create a link that opens in a new tab
                st.markdown(f'<a href="{url}" target="_blank">Open {section}{idx + 1:03}</a>', unsafe_allow_html=True)

# Function to process the uploaded file
def process_file(file_content, selected_base_url, is_image):
    # Read the file line by line
    lines = file_content.splitlines()
    data = {}  # Dictionary to store sections and their content
    current_section = None
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Check if the line starts with # (section header)
        if line.startswith('#'):
            current_section = line[1:].strip()  # Remove the # and any extra spaces
            if current_section not in data:
                data[current_section] = []  # Initialize a new section
        else:
            # Process the line as a photo name and URL
            if current_section is None:
                st.warning("Content without a section will be ignored. Add a section using #.")
                continue
            
            # Remove words followed by # in the line (if any)
            cleaned_line = ' '.join([word for word in line.split() if not word.endswith('#')])
            
            # Construct the link using the selected base URL and the cleaned line as the keyphrase
            search_url = selected_base_url.format(cleaned_line.replace(' ', '+'))
            
            # Add the content to the current section
            data[current_section].append((cleaned_line, search_url))
    
    # Display the content based on whether it's images or videos
    if is_image:
        display_images(data)
    else:
        display_videos(data)

# Function to compute a hash of the file content
def compute_file_hash(file_content):
    hasher = hashlib.sha256()
    hasher.update(file_content.encode('utf-8'))
    return hasher.hexdigest()

# Streamlit app
def main():
    st.title("Photo and Video Link Generator")
    st.write("Upload a text file to generate and open photo/video links based on its content.")

    # File uploader for the .py file containing base URLs
    uploaded_py_file = st.file_uploader("Upload a .py file containing IMAGE_BASE_URLS and VIDEO_BASE_URLS", type=["py"])

    if uploaded_py_file is not None:
        # Save the uploaded .py file temporarily
        with open("temp_base_urls.py", "wb") as f:
            f.write(uploaded_py_file.getbuffer())

        # Import the base URLs from the uploaded file
        try:
            IMAGE_BASE_URLS, VIDEO_BASE_URLS = import_base_urls_from_file("temp_base_urls.py")
            
            # Radio button to choose between images and videos
            content_type = st.radio("Select content type", ["Images", "Videos"])

            # Dropdown to select the base URL
            if content_type == "Images":
                selected_base_url_key = st.selectbox("Select an image base URL", list(IMAGE_BASE_URLS.keys()))
                selected_base_url = IMAGE_BASE_URLS[selected_base_url_key]
            else:
                selected_base_url_key = st.selectbox("Select a video base URL", list(VIDEO_BASE_URLS.keys()))
                selected_base_url = VIDEO_BASE_URLS[selected_base_url_key]

            # File uploader for the text file
            uploaded_txt_file = st.file_uploader("Choose a text file", type=["txt"])

            # Force Streamlit to reprocess the file if it changes
            if uploaded_txt_file is not None:
                # Read the file content
                file_content = uploaded_txt_file.read().decode('utf-8')
                
                # Compute a hash of the file content
                file_hash = compute_file_hash(file_content)
                
                # Check if the file has changed
                if "last_file_hash" not in st.session_state or st.session_state.last_file_hash != file_hash:
                    st.session_state.last_file_hash = file_hash
                    st.session_state.file_content = file_content
                
                # Reprocess the file if its content changes
                if "file_content" in st.session_state:
                    process_file(st.session_state.file_content, selected_base_url, content_type == "Images")

        except Exception as e:
            st.error(f"Failed to import base URLs from the uploaded file: {e}")

        # Clean up the temporary file
        os.remove("temp_base_urls.py")

if __name__ == "__main__":
    main()
