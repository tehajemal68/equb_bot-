import sqlite3

def init_db():
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()

    # 1. Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT
        )
    ''')

    # 2. Create Equb Groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equbs (
            equb_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            title TEXT,
            amount REAL,
            frequency TEXT,
            max_members INTEGER,
            status TEXT DEFAULT 'Open'
        )
    ''')

    # 3. Create Members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            equb_id INTEGER,
            user_id INTEGER,
            has_received_payout BOOLEAN DEFAULT 0,
            has_paid INTEGER DEFAULT 0,
            FOREIGN KEY(equb_id) REFERENCES equbs(equb_id),
            FOREIGN KEY(user_id) REFERENCES users(telegram_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Fresh database initialized successfully with payment tracking!")

if __name__ == "__main__":
    init_db()
