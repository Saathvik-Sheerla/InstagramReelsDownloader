import os
import time
import instaloader
import shutil
import subprocess

# Create an instance of Instaloader
L = instaloader.Instaloader()

def login(username, password):
    """
    Login to Instagram
    Args:
        username: Instagram username
        password: Instagram password
    """
    L.login(username, password)
    print(f"Logged in as {username}")

def download_reel(reel_url):
    """
    Download an Instagram reel in the best quality.
    Args:
        reel_url: URL of the Instagram reel
    Returns:
        str: Path to the downloaded file or error message
        int: Size of the downloaded file in bytes
    """
    try:
        # Extract the shortcode from the URL
        shortcode = reel_url.split("/reel/")[1].split("/")[0] if '/reel/' in reel_url else reel_url.split("/p/")[1].split("/")[0]
        
        print(f"Attempting to download reel with shortcode: {shortcode}")
        
        # Download the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Create a temporary directory for download
        temp_dir = f"temp_reel_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download the post to the temporary directory
        L.download_post(post, target=temp_dir)
        
        # Find the video file in the temporary directory
        video_file = None
        for file in os.listdir(temp_dir):
            if file.endswith(".mp4"):
                video_file = os.path.join(temp_dir, file)
                break
        
        if not video_file:
            shutil.rmtree(temp_dir)
            return "No video file found in the downloaded content", 0
        
        # Define the destination directory
        dest_dir = "./downloads"
        os.makedirs(dest_dir, exist_ok=True)
        
        # Set output file name
        output_file = os.path.join(dest_dir, f"instagram_reel_{int(time.time())}.mp4")

        # Copy the video file to the destination (no quality conversion)
        shutil.copy2(video_file, output_file)

        # Clean up temporary files
        shutil.rmtree(temp_dir)
        
        return output_file, os.path.getsize(output_file)
    
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return f"Error downloading reel: {e}", 0