import sqlite3
import os

def create_tables():
    """Connects to the database and creates the necessary tables."""
    script_dir = os.path.dirname(os.path.abspath(__file__)) # Get the directory where the script is located
    db_path = os.path.join(script_dir, '..', 'database', 'money_manager.db')

    # Ensure the target database directory exists
    target_db_dir = os.path.dirname(db_path)
    os.makedirs(target_db_dir, exist_ok=True)

    abs_db_path = os.path.abspath(db_path)
    print(f"Script directory: {script_dir}")
    print(f"Target database directory: {target_db_dir}")
    print(f"Absolute path to database file: {abs_db_path}")

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        conn.commit()
        print(f"Database '{db_path}' and tables created successfully.")

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_tables()
