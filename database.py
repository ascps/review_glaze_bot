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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            name TEXT,
            subscribed BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

def add_giveaway_participant(user_id, username, name):
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Проверяем существующую запись
        cursor.execute('SELECT 1 FROM giveaway_participants WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"Участник {user_id} уже существует")
            return False
            
        cursor.execute('''
            INSERT INTO giveaway_participants 
            (user_id, username, name, subscribed) 
            VALUES (?, ?, ?, 1)
        ''', (user_id, username, name))
        
        conn.commit()
        logger.info(f"Участник {user_id} успешно добавлен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка добавления участника: {e}")
        return False
    finally:
        conn.close()

def get_giveaway_participants():
    conn = sqlite3.connect(Config.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, username, name FROM giveaway_participants WHERE subscribed = 1')
    participants = cursor.fetchall()
    
    conn.close()
    return [{'user_id': p[0], 'username': p[1], 'name': p[2]} for p in participants]

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