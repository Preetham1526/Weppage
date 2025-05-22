import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # ------------------- USERS TABLE -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            country TEXT,
            state TEXT,
            password TEXT NOT NULL
        )
    """)

    # ------------------- OTP TABLE -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_tokens (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ------------------- DISCUSSIONS TABLE -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------- DISCUSSION REPLIES -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discussion_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discussion_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            reply TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (discussion_id) REFERENCES discussions(id)
        )
    """)

    # ------------------- CAREERS TABLE -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            full_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            resume_link TEXT,
            cover_letter TEXT,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)

    # ------------------- CONTACT MESSAGES TABLE -------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------- OPTIONAL: SUBSCRIPTIONS TABLE -------------------
    # If you want to store a mirror of MongoDB subscriptions in SQLite
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            plan TEXT NOT NULL,
            price REAL NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            payment_method TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
