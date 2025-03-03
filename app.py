import os
import telebot
import re
from telebot import types
import time
import instaloader
import shutil
from dotenv import load_dotenv

load_dotenv()

telebot.apihelper.ENABLE_MIDDLEWARE = True

# Initialize Telegram bot 
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN') 
bot = telebot.TeleBot(BOT_API_TOKEN)

# Create an instance of Instaloader
L = instaloader.Instaloader()

# This function is from your original code
def download_reel(reel_url):
    """
    Download an Instagram reel given its URL
    Args:
        reel_url: URL of the Instagram reel
    Returns:
        str: Path to the downloaded file or error message
    """
    try:
        # Extract the shortcode from the URL
        if '/reel/' in reel_url:
            shortcode = reel_url.split("/reel/")[1].split("/")[0]
        else:
            shortcode = reel_url.split("/p/")[1].split("/")[0]
        
        print(f"Attempting to download reel with shortcode: {shortcode}")
        
        # Download the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Create a temporary directory for download
        temp_dir = f"temp_reel_{int(time.time())}"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Download the post to the temporary directory
        L.download_post(post, target=temp_dir)
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.expanduser("./downloads")
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        # Find the video file in the temporary directory
        for file in os.listdir(temp_dir):
            if file.endswith(".mp4"):
                source_file = os.path.join(temp_dir, file)
                dest_file = os.path.join(dest_dir, f"reel_{int(time.time())}.mp4")
                
                # Copy the file to the destination with the desired name
                shutil.copy2(source_file, dest_file)
                
                # Clean up the temporary directory
                shutil.rmtree(temp_dir)
                
                return dest_file, os.path.getsize(dest_file)  # Return file path and size
        
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        return "No video file found in the downloaded content", 0
    
    except Exception as e:
        error_message = f"Error downloading reel: {e}"
        print(error_message)
        return error_message, 0

# Define regex pattern for Instagram reel URLs
INSTAGRAM_PATTERN = r'(https?://(www\.)?instagram\.com/(p|reel)/[a-zA-Z0-9_-]+)'

# Command handler for /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Instagram Reel Downloader Bot! developed by Saathvik Sheerla, Just send me an Instagram reel URL, and I'll download it for you.")

# Command handler for /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
This bot downloads Instagram reels for you!

How to use:
1. Simply paste an Instagram reel URL like https://www.instagram.com/reel/example/
2. The bot will download and send you the video

Note: Very large videos may not be sent due to Telegram limitations (max 50MB for standard bots).
For any issues, contact the administrator.
    """
    bot.reply_to(message, help_text)

# Command handler for Instagram login (optional)
@bot.message_handler(commands=['login'])
def login_command(message):
    msg = bot.reply_to(message, "Enter your Instagram username:")
    bot.register_next_step_handler(msg, process_username_step)

def process_username_step(message):
    username = message.text
    msg = bot.reply_to(message, "Enter your Instagram password:")
    bot.register_next_step_handler(msg, lambda m: process_password_step(m, username))

def process_password_step(message, username):
    try:
        # Delete the message with password for security
        bot.delete_message(message.chat.id, message.message_id)
        
        password = message.text
        L.login(username, password)
        bot.send_message(message.chat.id, "Login successful! You can now download reels with higher success rate.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Login failed: {e}")

# Handle all messages that might contain Instagram URLs
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Check if message contains an Instagram URL
    matches = re.findall(INSTAGRAM_PATTERN, message.text)
    
    if matches:
        url = matches[0][0]  # Get the full URL from the first match
        status_message = bot.reply_to(message, "Downloading reel... Please wait.")
        
        # Download the reel using your existing function
        result, file_size = download_reel(url)
        
        if isinstance(result, str) and (result.startswith("Error") or result.startswith("No video")):
            bot.edit_message_text(result, message.chat.id, status_message.message_id)
        else:
            # Calculate file size in MB
            file_size_mb = file_size / (1024 * 1024)
            
            # Check if file is too large for Telegram (50MB limit for bots)
            if file_size_mb > 50:
                bot.edit_message_text(
                    f"The video is too large to send via Telegram ({file_size_mb:.1f}MB). "
                    f"Telegram bots can only send files up to 50MB.", 
                    message.chat.id, 
                    status_message.message_id
                )
                # Don't delete the file so user can handle it manually if needed
                # Add file path to the message
                bot.send_message(message.chat.id, f"File saved at: {result}")
            else:
                # Send the video file with increased timeout and retry mechanism
                try:
                    # Update status
                    bot.edit_message_text(
                        f"Download complete! Sending video ({file_size_mb:.1f}MB)...", 
                        message.chat.id, 
                        status_message.message_id
                    )
                    
                    # Try to send the video with multiple attempts
                    max_attempts = 3
                    for attempt in range(1, max_attempts + 1):
                        try:
                            with open(result, 'rb') as video:
                                sent_message = bot.send_video(
                                    message.chat.id, 
                                    video, 
                                    caption="Here's your Instagram reel!",
                                    timeout=60  # Increase timeout to 60 seconds
                                )
                            # If successful, break the loop
                            bot.delete_message(message.chat.id, status_message.message_id)
                            # Clean up the file after sending
                            os.remove(result)
                            break
                        except Exception as e:
                            if attempt < max_attempts:
                                # Update status with retry information
                                bot.edit_message_text(
                                    f"Sending failed, retrying ({attempt}/{max_attempts})...", 
                                    message.chat.id, 
                                    status_message.message_id
                                )
                                time.sleep(2)  # Wait before retrying
                            else:
                                # Final failure after all attempts
                                bot.edit_message_text(
                                    f"Error sending video after {max_attempts} attempts: {e}\n"
                                    f"The video has been saved at: {result}",
                                    message.chat.id, 
                                    status_message.message_id
                                )
                except Exception as e:
                    bot.edit_message_text(
                        f"Error sending video: {e}\nThe video has been saved at: {result}", 
                        message.chat.id, 
                        status_message.message_id
                    )
    else:
        bot.reply_to(message, "Please send a valid Instagram reel URL. Example: https://www.instagram.com/reel/example/")

# Add an error handler for request timeouts
@bot.middleware_handler(update_types=['message'])
def handle_timeout_error(bot_instance, update):
    try:
        # This runs before each message is processed
        pass
    except telebot.apihelper.ApiTelegramException as e:
        if "timed out" in str(e).lower():
            print("Request timed out. Network might be slow.")
        else:
            raise

if __name__ == '__main__':
    print("Bot started...")
    
    # Configure telebot for longer timeouts
    telebot.apihelper.CONNECT_TIMEOUT = 30
    telebot.apihelper.READ_TIMEOUT = 60
    
    # Start the bot with more robust error handling
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(15)  # Wait before trying to reconnect