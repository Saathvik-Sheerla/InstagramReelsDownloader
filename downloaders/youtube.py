import os
import time
import subprocess

def download_video(video_url):
    try:
        # Ensure the downloads directory exists
        dest_dir = os.path.expanduser("./downloads")
        os.makedirs(dest_dir, exist_ok=True)
        
        # Generate a unique filename for the downloaded video
        output_filename = f"youtube_video_{int(time.time())}.mp4"
        output_path = os.path.join(dest_dir, output_filename)
        
        # Run yt-dlp to download the best available video with audio
        command = ['yt-dlp', '-f', 'best', '-o', output_path, '--no-playlist', video_url]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        # Verify if the video file was successfully downloaded
        if os.path.exists(output_path):
            return output_path, os.path.getsize(output_path)
        
        return "Error: Video download failed", 0
    except subprocess.CalledProcessError:
        return "Error: Video download failed", 0
    except Exception as e:
        return f"Error: {e}", 0
