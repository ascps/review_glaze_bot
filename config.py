import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')
    DB_NAME = 'reviews.db'