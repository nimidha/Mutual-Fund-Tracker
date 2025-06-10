# database.py
import sqlite3

def create_connection():
    conn = sqlite3.connect('users.db')
    return conn

def create_users_table():
    conn = create_connection()
    cursor = conn.cursor()

    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def create_funds_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            username TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
