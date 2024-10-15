import sqlite3
from datetime import datetime

from .bottle_messages import BottleMessagesDB
from .quotes import Quotes

class DB(
    BottleMessagesDB,
    Quotes
): 
    def __init__(self, db_name='botoy.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()
        
    def create_table(self):
        self.cursor.execute('''
        -- bottle_messages
        CREATE TABLE IF NOT EXISTS bottle_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            group_id INTEGER,
            group_name TEXT,
            text TEXT,
            imgs TEXT,  -- 使用 JSON 存储列表
            time TEXT   -- %Y-%m-%d %H:%M:%S
        )
        
        -- quotes
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT,
            group_id INTEGER,
            img TEXT,  -- 保存图片base64编码
            time TEXT   -- %Y-%m-%d %H:%M:%S
        )
        ''')
        self.conn.commit()
        
    def insert_data(self, table, **kwargs):
        self.cursor.execute('''
            INSERT INTO {} {}
            VALUES {}
        '''.format(table, str(tuple(kwargs.keys())), str(tuple(kwargs.values()))))
        self.conn.commit()

    def fetch_all(self, table):
        self.cursor.execute('SELECT * FROM {}'.format(table))
        return self.cursor.fetchall()

    def fetch_by_id(self, table, where):
        self.cursor.execute('SELECT * FROM {} WHERE {}'.format(table, where))
        return self.cursor.fetchone()

    def update_data(self, table, where, update_data):
        updates = []
        for k, v in update_data.items():
            updates.append('{} = {}'.format(v))
        updates = ', '.join(updates)
        
        self.cursor.execute('''
            UPDATE {} SET {} WHERE {}
        '''.format(table, updates, where))
        self.conn.commit()

    def delete_data(self, table, where):
        self.cursor.execute('DELETE FROM {} WHERE {}'.format(table, where))
        self.conn.commit()
    
    @staticmethod
    def datetime2str(time):
        return datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def str2datetime(datetime_str):
        return datetime.strptime(datetime_str)

db = DB()