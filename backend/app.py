import sqlite3
import os
from flask import Flask, jsonify, request

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Database Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(SCRIPT_DIR, '..', 'database', 'money_manager.db')

def get_db_connection():
    """Connects to the SQLite database and returns a connection object."""
    if not os.path.exists(DATABASE_PATH):
        # This should ideally not happen if database_setup.py ran
        print(f"CRITICAL: Database file not found at {DATABASE_PATH}.")
        # In a real Flask app, you might want to ensure the DB is set up
        # or raise a more specific Flask error.
        # For now, we proceed, and functions will fail if DB isn't there.
        pass
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Category Functions (Original logic, adapted for Flask context if needed) ---
def add_category_db(name):
    """Adds a new category to the categories table. Renamed to avoid conflict."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # This will be caught by the route and returned as a 409 or similar
        raise
    finally:
        if conn:
            conn.close()

def get_categories_db():
    """Queries and returns all rows from the categories table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()
        return [dict(row) for row in categories]
    finally:
        if conn:
            conn.close()

# --- Transaction Functions (Original logic, adapted for Flask context if needed) ---
def add_transaction_db(date, description, type, amount, category_id):
    """Adds a new transaction. Renamed to avoid conflict."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, description, type, amount, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (date, description, type, amount, category_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        if conn:
            conn.close()

def get_all_transactions_db():
    """Queries and returns all transactions, joining with categories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.date, t.description, t.type, t.amount, c.name as category_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            ORDER BY t.date DESC
        """)
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    finally:
        if conn:
            conn.close()

def get_transactions_by_type_db(transaction_type):
    """Queries and returns transactions filtered by type."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.date, t.description, t.type, t.amount, c.name as category_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = ?
            ORDER BY t.date DESC
        """, (transaction_type,))
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    finally:
        if conn:
            conn.close()

def get_transactions_by_category_db(category_id):
    """Queries and returns transactions for a specific category."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.date, t.description, t.type, t.amount, c.name as category_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.category_id = ?
            ORDER BY t.date DESC
        """, (category_id,))
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    finally:
        if conn:
            conn.close()

def get_balance_db():
    """Calculates and returns total income, total expenses, and net balance."""
    total_income = 0.0
    total_expense = 0.0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_income = result[0]
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_expense = result[0]
        net_balance = total_income - total_expense
        return {'total_income': total_income, 'total_expense': total_expense, 'net_balance': net_balance}
    finally:
        if conn:
            conn.close()

def delete_transaction_db(transaction_id):
    """Deletes a transaction from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0 # Returns true if a row was deleted
    finally:
        if conn:
            conn.close()

def update_transaction_db(transaction_id, date, description, type, amount, category_id):
    """Updates an existing transaction in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions
            SET date = ?, description = ?, type = ?, amount = ?, category_id = ?
            WHERE id = ?
        """, (date, description, type, amount, category_id, transaction_id))
        conn.commit()
        return cursor.rowcount > 0 # Returns true if a row was updated
    finally:
        if conn:
            conn.close()

# --- Flask API Routes ---

@app.route('/categories', methods=['POST'])
def api_add_category():
    data = request.get_json()
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({'error': 'Category name is required'}), 400
    name = data['name'].strip()
    try:
        category_id = add_category_db(name)
        return jsonify({'id': category_id, 'name': name}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': f"Category '{name}' already exists"}), 409 # Conflict
    except Exception as e:
        app.logger.error(f"Error adding category: {e}")
        return jsonify({'error': 'Failed to add category'}), 500

@app.route('/categories', methods=['GET'])
def api_get_categories():
    try:
        categories = get_categories_db()
        return jsonify(categories)
    except Exception as e:
        app.logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Failed to retrieve categories'}), 500

@app.route('/transactions', methods=['POST'])
def api_add_transaction():
    data = request.get_json()
    required_fields = ['date', 'description', 'type', 'amount', 'category_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields for transaction'}), 400

    if data['type'] not in ('income', 'expense'):
        return jsonify({'error': "Transaction type must be 'income' or 'expense'"}), 400

    try:
        # Basic validation for amount
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    try:
        # Check if category_id exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (data['category_id'],))
        category = cursor.fetchone()
        conn.close()
        if not category:
            return jsonify({'error': f"Category with id {data['category_id']} not found"}), 400

        transaction_id = add_transaction_db(
            data['date'], data['description'], data['type'], amount, data['category_id']
        )
        # Return the full transaction object as it would be from a GET
        new_transaction_data = {
            'id': transaction_id,
            'date': data['date'],
            'description': data['description'],
            'type': data['type'],
            'amount': amount,
            'category_id': data['category_id']
            # category_name could be fetched and added here if desired for POST response
        }
        return jsonify(new_transaction_data), 201
    except Exception as e:
        app.logger.error(f"Error adding transaction: {e}")
        return jsonify({'error': 'Failed to add transaction'}), 500

@app.route('/transactions', methods=['GET'])
def api_get_all_transactions():
    try:
        transactions = get_all_transactions_db()
        return jsonify(transactions)
    except Exception as e:
        app.logger.error(f"Error getting all transactions: {e}")
        return jsonify({'error': 'Failed to retrieve transactions'}), 500

@app.route('/transactions/type/<string:transaction_type>', methods=['GET'])
def api_get_transactions_by_type(transaction_type):
    if transaction_type not in ('income', 'expense'):
        return jsonify({'error': "Invalid transaction type. Must be 'income' or 'expense'."}), 400
    try:
        transactions = get_transactions_by_type_db(transaction_type)
        return jsonify(transactions)
    except Exception as e:
        app.logger.error(f"Error getting transactions by type: {e}")
        return jsonify({'error': f"Failed to retrieve {transaction_type} transactions"}), 500

@app.route('/transactions/category/<int:category_id>', methods=['GET'])
def api_get_transactions_by_category(category_id):
    try:
        # Check if category_id exists before querying transactions
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        category = cursor.fetchone()
        conn.close()
        if not category:
            return jsonify({'error': f"Category with id {category_id} not found"}), 404

        transactions = get_transactions_by_category_db(category_id)
        return jsonify(transactions)
    except Exception as e:
        app.logger.error(f"Error getting transactions by category: {e}")
        return jsonify({'error': f"Failed to retrieve transactions for category {category_id}"}), 500

@app.route('/balance', methods=['GET'])
def api_get_balance():
    try:
        balance_data = get_balance_db()
        return jsonify(balance_data)
    except Exception as e:
        app.logger.error(f"Error getting balance: {e}")
        return jsonify({'error': 'Failed to retrieve balance'}), 500

@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def api_delete_transaction(transaction_id):
    try:
        if delete_transaction_db(transaction_id):
            return jsonify({'message': 'Transaction deleted successfully'}), 200
        else:
            return jsonify({'error': 'Transaction not found or already deleted'}), 404
    except Exception as e:
        app.logger.error(f"Error deleting transaction {transaction_id}: {e}")
        return jsonify({'error': 'Failed to delete transaction'}), 500

@app.route('/transactions/<int:transaction_id>', methods=['PUT'])
def api_update_transaction(transaction_id):
    data = request.get_json()
    required_fields = ['date', 'description', 'type', 'amount', 'category_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields for transaction update'}), 400

    if data['type'] not in ('income', 'expense'):
        return jsonify({'error': "Transaction type must be 'income' or 'expense'"}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    try:
        # Check if category_id exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = ?", (data['category_id'],))
        category = cursor.fetchone()
        conn.close() # Close this connection
        if not category:
            return jsonify({'error': f"Category with id {data['category_id']} not found"}), 400

        if update_transaction_db(transaction_id, data['date'], data['description'], data['type'], amount, data['category_id']):
            updated_data = {
                'id': transaction_id,
                'date': data['date'],
                'description': data['description'],
                'type': data['type'],
                'amount': amount,
                'category_id': data['category_id']
            }
            return jsonify({'message': 'Transaction updated successfully', 'transaction': updated_data}), 200
        else:
            # This could be because the transaction_id itself doesn't exist
            return jsonify({'error': 'Transaction not found or no changes made'}), 404
    except Exception as e:
        app.logger.error(f"Error updating transaction {transaction_id}: {e}")
        return jsonify({'error': 'Failed to update transaction'}), 500

# --- Initialization Function (from original script) ---
def initialize_defaults():
    """Initializes default categories if none exist."""
    print("Initializing defaults for Flask app...")
    # Need to use the DB functions that return list of dicts or handle Row objects
    conn_check = False
    try:
        # Quick check if DB exists and categories table is queryable
        # This is to prevent error during Flask startup if DB is not yet created
        if not os.path.exists(DATABASE_PATH):
            print(f"Database not found at {DATABASE_PATH}. Skipping default initialization. Run database_setup.py.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories';")
        if not cursor.fetchone():
            print("Categories table not found. Skipping default initialization. Run database_setup.py.")
            conn.close()
            return
        conn.close() # Close this initial check connection

        categories = get_categories_db() # This uses its own connection
        if not categories:
            print("No categories found. Adding default categories.")
            default_categories = ['Salary', 'Groceries', 'Bills', 'Rent', 'Entertainment', 'Transport', 'Healthcare', 'Other']
            for cat_name in default_categories:
                try:
                    add_category_db(cat_name) # Use the DB function
                    print(f"Added default category: {cat_name}")
                except sqlite3.IntegrityError:
                    print(f"Default category {cat_name} already exists.")
                except Exception as e:
                    print(f"Error adding default category {cat_name}: {e}")
        else:
            print("Categories already exist, skipping default additions.")
    except sqlite3.Error as e:
        print(f"SQLite error during initialization: {e}. Ensure database and tables are created via database_setup.py.")
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")


if __name__ == '__main__':
    # Ensure database and tables are created before starting the Flask app
    if not os.path.exists(DATABASE_PATH):
        print(f"ERROR: Database file not found at {DATABASE_PATH}")
        print("Please run 'python backend/database_setup.py' to create the database and tables first.")
    else:
        # Check if tables exist, basic check.
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories';")
            if not cursor.fetchone():
                 print(f"ERROR: 'categories' table not found in {DATABASE_PATH}.")
                 print("Please run 'python backend/database_setup.py' to create the database and tables first.")
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
                if not cursor.fetchone():
                    print(f"ERROR: 'transactions' table not found in {DATABASE_PATH}.")
                    print("Please run 'python backend/database_setup.py' to create the database and tables first.")
                else:
                    print("Database and tables seem to be in place.")
                    initialize_defaults()
                    app.run(host='0.0.0.0', port=5000, debug=True)
            if conn:
                conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error checking tables: {e}. Make sure database_setup.py has run successfully.")
        except Exception as e:
            print(f"Failed to start Flask app due to an error: {e}")
