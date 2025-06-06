import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8443))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Userbot Configuration
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER')
    
    # Admin Configuration
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    
    # Bot Settings
    MAX_TASKS = 50
    MAX_DELAY = 3600  # 1 hour max delay
    SUPPORTED_MEDIA_TYPES = [
        'photo', 'video', 'audio', 'document', 
        'voice', 'video_note', 'sticker', 'animation'
    ]
