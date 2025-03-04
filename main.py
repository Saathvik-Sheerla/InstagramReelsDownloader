import os
import telebot
import re
import time
import hashlib
import logging
from telebot import types
from dotenv import load_dotenv
import downloaders.instagram as instagram_downloader
import downloaders.youtube as youtube_downloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Enable middleware for additional processing
telebot.apihelper.ENABLE_MIDDLEWARE = True

# Initialize Telegram bot with API token
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN_TEST') 
bot = telebot.TeleBot(BOT_API_TOKEN)

# Regular expression patterns to detect URLs
INSTAGRAM_PATTERN = r'(https?://(www\.)?instagram\.com/(p|reel)/[a-zA-Z0-9_-]+)'
YOUTUBE_PATTERN = r'(https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+)'

# Ensure the downloads directory exists
if not os.path.exists('./downloads'):
    os.makedirs('./downloads')

# Command handler for /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Media Downloader Bot! Send an Instagram reel or YouTube video URL, and I'll download it for you.")

# Command handler for /help command
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
This bot downloads Instagram reels and YouTube videos for you!

How to use:
1. For Instagram: Paste an Instagram reel URL.
2. For YouTube: Paste a YouTube video URL.
3. The bot will automatically download the best available quality.
    """
    bot.reply_to(message, help_text)

# Handle messages containing URLs
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    instagram_matches = re.findall(INSTAGRAM_PATTERN, message.text)
    youtube_matches = re.findall(YOUTUBE_PATTERN, message.text)
    
    if instagram_matches:
        url = instagram_matches[0][0]  # Extract Instagram URL
        logging.info(f"Downloading Instagram reel: {url}")
        bot.send_message(message.chat.id, "Downloading Instagram reel in the best quality...")
        file_path, file_size = instagram_downloader.download_reel(url)
        logging.info(f"Downloaded Instagram reel: {file_path}, Size: {file_size} bytes")
        send_and_cleanup(message, file_path, file_size)
    
    elif youtube_matches:
        url = youtube_matches[0][0]  # Extract YouTube URL
        logging.info(f"Downloading YouTube video: {url}")
        bot.send_message(message.chat.id, "Downloading YouTube video in the best quality...")
        file_path, file_size = youtube_downloader.download_video(url)
        logging.info(f"Downloaded YouTube video: {file_path}, Size: {file_size / (1024 * 1024):.2f}MB")
        send_and_cleanup(message, file_path, file_size)
    else:
        bot.reply_to(message, "Send a valid Instagram or YouTube URL.")

# Function to send the downloaded file and clean up afterward
def send_and_cleanup(message, file_path, file_size):
    file_size_mb = file_size / (1024 * 1024)  # Convert file size to MB
    
    if file_size_mb > 50:
        bot.send_message(message.chat.id, f"File too large ({file_size_mb:.1f}MB). Sorry, cannot download files larger 50MB, I'm working on this feature in future updates you can download larger files :)")
        logging.warning(f"File too large to send: {file_path}, Size: {file_size_mb:.1f}MB")
    else:
        with open(file_path, 'rb') as file:
            if file_path.endswith('.mp4'):
                bot.send_video(message.chat.id, file, caption="Here is your video!")
            elif file_path.endswith('.mp3'):
                bot.send_audio(message.chat.id, file, caption="Here is your audio!")
        logging.info(f"Sent file to user: {file_path}")
    
    # Auto-delete file after sending
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")

# Start the bot when the script runs
if __name__ == '__main__':
    logging.info("Bot started...")
    bot.polling(none_stop=True, timeout=60)
