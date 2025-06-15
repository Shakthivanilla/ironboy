# Simple Money Management App (INR)

A simple web application for managing personal income and expenses, with all monetary values in INR.

## Features

*   Track income and expenses.
*   Categorize transactions.
*   View current balance (total income, total expenses, net balance).
*   Add, Edit, and Delete transactions.
*   Responsive basic UI for web browsers.

## Technology Stack

*   **Backend:** Python (Flask)
*   **Database:** SQLite
*   **Frontend:** HTML, CSS, JavaScript (no external frameworks)

## Prerequisites

*   Python 3.x
*   pip (Python package installer)

## Setup and Running the Application

1.  **Clone the repository (if applicable) or download the files.**
    ```bash
    # If this were a git repo, you'd clone it
    # git clone <repository-url>
    # cd <repository-name>
    ```

2.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

4.  **Install dependencies:**
    The only external dependency for the backend is Flask.
    ```bash
    pip install Flask
    ```

5.  **Run the Backend Server:**
    Still within the `backend` directory:
    ```bash
    python app.py
    ```
    This will typically start the Flask development server on `http://127.0.0.1:5000/`.
    The server will also create the `database/money_manager.db` file and initialize default categories if they don't exist. The necessary table structures are created by `app.py` on its first run if the database/tables are missing.

6.  **Open the Frontend in your Browser:**
    *   Navigate to the `frontend` directory in your file explorer.
    *   Open the `index.html` file directly in your web browser (e.g., by double-clicking it or using "Open with..." your browser).

    The application should now be running, with the frontend communicating with the backend server.

## Project Structure

```
.
├── backend/
│   ├── app.py              # Flask backend logic, API endpoints, and DB initialization
│   └── database_setup.py   # (Legacy - functionality integrated into app.py)
├── database/
│   └── money_manager.db    # SQLite database file (created automatically by app.py)
├── frontend/
│   ├── index.html          # Main application page
│   ├── script.js           # Frontend JavaScript logic
│   └── style.css           # CSS styles
└── README.md               # This file
```
