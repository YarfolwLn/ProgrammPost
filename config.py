import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Groq API
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    
    # VK
    VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN')
    VK_GROUP_ID = os.getenv('VK_GROUP_ID')
    VK_API_VERSION = os.getenv('VK_API_VERSION', '5.199')
    
    # Instagram
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    
    # TikTok
    TIKTOK_API_KEY = os.getenv('TIKTOK_API_KEY')
    
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'posts.db')
    
    # Images
    IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
    GENERATED_IMAGES_DIR = os.path.join(IMAGES_DIR, 'generated')
    
    # Scheduler
    POST_TIMES = ['09:00', '18:00']  # 2 раза в день
    
    # Quote image settings
    QUOTE_IMAGE_WIDTH = 1080
    QUOTE_IMAGE_HEIGHT = 1080
    QUOTE_FONT_SIZE = 36
    AUTHOR_FONT_SIZE = 24
    BACKGROUND_COLOR = (20, 20, 20)  # Темно-серый, почти черный
    TEXT_COLOR = (255, 255, 255)  # Белый
    AUTHOR_COLOR = (200, 200, 200)  # Светло-серый
