import sqlite3
import os
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.ensure_database_exists()
        self.create_tables()
    
    def ensure_database_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица цитат
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote TEXT NOT NULL,
                    author TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used_count INTEGER DEFAULT 0
                )
            ''')
            
            # Миграция: добавляем image_path если колонки нет
            cursor.execute("PRAGMA table_info(quotes)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'image_path' not in columns:
                cursor.execute('ALTER TABLE quotes ADD COLUMN image_path TEXT')
                conn.commit()
            
            # Таблица постов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id INTEGER,
                    title TEXT,
                    content TEXT NOT NULL,
                    image_path TEXT,
                    platforms TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    scheduled_time TIMESTAMP,
                    posted_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (quote_id) REFERENCES quotes (id)
                )
            ''')
            
            # Таблица логов публикаций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')
            
            conn.commit()
    
    def add_quote(self, quote: str, author: str, description: str, image_path: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quotes (quote, author, description, image_path)
                VALUES (?, ?, ?, ?)
            ''', (quote, author, description, image_path))
            conn.commit()
            return cursor.lastrowid
    
    def get_quote(self, quote_id: int) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, quote, author, description, image_path, created_at, used_count FROM quotes WHERE id = ?', (quote_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'quote': row[1],
                    'author': row[2],
                    'description': row[3],
                    'image_path': row[4],
                    'created_at': row[5],
                    'used_count': row[6]
                }
            return None
    
    def get_all_quotes(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, quote, author, description, image_path, created_at, used_count FROM quotes ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'quote': row[1],
                'author': row[2],
                'description': row[3],
                'image_path': row[4],
                'created_at': row[5],
                'used_count': row[6]
            } for row in rows]
    
    def get_random_unused_quote(self) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, quote, author, description, created_at, used_count 
                FROM quotes 
                WHERE used_count = 0 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'quote': row[1],
                    'author': row[2],
                    'description': row[3],
                    'created_at': row[4],
                    'used_count': row[5]
                }
            return None
    
    def increment_quote_usage(self, quote_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE quotes SET used_count = used_count + 1 WHERE id = ?', (quote_id,))
            conn.commit()
    
    def update_quote_image_path(self, quote_id: int, image_path: str):
        """Обновляет путь к изображению для цитаты"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE quotes SET image_path = ? WHERE id = ?', (image_path, quote_id))
            conn.commit()
    
    def delete_quote(self, quote_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM quotes WHERE id = ?', (quote_id,))
            conn.commit()
    
    def add_post(self, quote_id: int, title: str, content: str, image_path: str, platforms: list, scheduled_time: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO posts (quote_id, title, content, image_path, platforms, scheduled_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (quote_id, title, content, image_path, ','.join(platforms), scheduled_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_post(self, post_id: int) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, quote_id, title, content, image_path, platforms, status, scheduled_time, posted_time, created_at
                FROM posts WHERE id = ?
            ''', (post_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'quote_id': row[1],
                    'title': row[2],
                    'content': row[3],
                    'image_path': row[4],
                    'platforms': row[5].split(',') if row[5] else [],
                    'status': row[6],
                    'scheduled_time': row[7],
                    'posted_time': row[8],
                    'created_at': row[9]
                }
            return None
    
    def get_pending_posts(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, quote_id, title, content, image_path, platforms, status, scheduled_time, posted_time, created_at
                FROM posts WHERE status = 'pending' AND scheduled_time <= datetime('now')
                ORDER BY scheduled_time
            ''')
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'quote_id': row[1],
                'title': row[2],
                'content': row[3],
                'image_path': row[4],
                'platforms': row[5].split(',') if row[5] else [],
                'status': row[6],
                'scheduled_time': row[7],
                'posted_time': row[8],
                'created_at': row[9]
            } for row in rows]
    
    def get_all_posts(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, quote_id, title, content, image_path, platforms, status, scheduled_time, posted_time, created_at
                FROM posts ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'quote_id': row[1],
                'title': row[2],
                'content': row[3],
                'image_path': row[4],
                'platforms': row[5].split(',') if row[5] else [],
                'status': row[6],
                'scheduled_time': row[7],
                'posted_time': row[8],
                'created_at': row[9]
            } for row in rows]
    
    def update_post_status(self, post_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            posted_time = datetime.now().isoformat() if status == 'posted' else None
            cursor.execute('''
                UPDATE posts SET status = ?, posted_time = ? WHERE id = ?
            ''', (status, posted_time, post_id))
            conn.commit()
    
    def add_post_log(self, post_id: int, platform: str, status: str, error_message: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO post_logs (post_id, platform, status, error_message)
                VALUES (?, ?, ?, ?)
            ''', (post_id, platform, status, error_message))
            conn.commit()
    
    def get_post_logs(self, post_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, post_id, platform, status, error_message, posted_at
                FROM post_logs WHERE post_id = ? ORDER BY posted_at DESC
            ''', (post_id,))
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'post_id': row[1],
                'platform': row[2],
                'status': row[3],
                'error_message': row[4],
                'posted_at': row[5]
            } for row in rows]
