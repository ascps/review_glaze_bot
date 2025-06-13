import sqlite3
from config import Config
import logging

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            screenshot_path TEXT,
            review_date TEXT,
            reviewer_name TEXT,
            article TEXT,
            payment_info TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Проверяем существование столбца payment_info и добавляем его, если нужно
    cursor.execute("PRAGMA table_info(reviews)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'payment_info' not in columns:
        cursor.execute("ALTER TABLE reviews ADD COLUMN payment_info TEXT")
    
    conn.commit()
    conn.close()

def add_review(data):
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO reviews (
            user_id, username, screenshot_path, 
            review_date, reviewer_name, article, payment_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['user_id'], data['username'], data['screenshot_path'],
        data['review_date'], data['reviewer_name'], data['article'], data['payment_info']
    ))
    
    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id

def get_review_by_id(review_id):
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM reviews WHERE id = ?', (review_id,))
    review = cursor.fetchone()
    
    conn.close()
    
    if review:
        return {
            'id': review[0],
            'user_id': review[1],
            'username': review[2],
            'screenshot_path': review[3],
            'review_date': review[4],
            'reviewer_name': review[5],
            'article': review[6],
            'payment_info': review[7],
            'status': review[8],
            'created_at': review[9]
        }
    return None

def update_review_status(review_id, status):
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reviews SET status = ? WHERE id = ?
    ''', (status, review_id))
    
    conn.commit()
    conn.close()