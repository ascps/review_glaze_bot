import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')
    CHANNEL_ID = os.getenv('CHANNEL_ID')  # ID канала для проверки подписки
    DB_NAME = 'reviews.db'