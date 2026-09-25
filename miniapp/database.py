import os
import sqlite3

DB_NAME = os.getenv("DB_NAME", "duyes.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        language TEXT DEFAULT 'ru',
        gender TEXT,
        name TEXT,
        birth_date TEXT,
        country TEXT,
        country_code TEXT,
        region TEXT,
        city TEXT,
        latitude REAL,
        longitude REAL,
        previously_married INTEGER DEFAULT 0,
        children INTEGER DEFAULT 0,
        about TEXT,
        photo_1_file_id TEXT,
        photo_2_file_id TEXT,
        photos_hidden INTEGER DEFAULT 0,
        profile_published INTEGER DEFAULT 0,
        profile_blocked INTEGER DEFAULT 0,
        test_account INTEGER DEFAULT 0,
        photo_rules_accepted INTEGER DEFAULT 0,
        online INTEGER DEFAULT 0,
        last_seen TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        verification_status TEXT DEFAULT 'none',
        verification_submitted_at TEXT,
        verification_verified_at TEXT,
        verification_rejection_reason TEXT,
        subscription_status TEXT DEFAULT 'free',
        subscription_plan TEXT,
        subscription_started_at TEXT,
        subscription_expires_at TEXT,
        trial_started_at TEXT,
        trial_expires_at TEXT,
        payment_id TEXT,
        subscription_currency TEXT,
        subscription_amount REAL
    );

    CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        favorite_user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, favorite_user_id)
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS gifts (
        gift_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emoji TEXT,
        name_ru TEXT,
        name_hy TEXT,
        name_en TEXT,
        name_fr TEXT,
        price_coins INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        image_path TEXT
    );

    CREATE TABLE IF NOT EXISTS gift_balances (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS gift_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        transaction_type TEXT NOT NULL,
        gift_id INTEGER,
        related_user_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sent_gifts (
        gift_send_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        gift_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        viewed INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER DEFAULT 0
    );
    ''')
    conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('GIFTS_ENABLED','1')")
    conn.commit()
    conn.close()


init_db()
