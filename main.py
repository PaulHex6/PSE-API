# main.py
# Entry point to initialize the database and start the Streamlit app.

from code.db import init_db
from frontend.app import main

if __name__ == "__main__":
    init_db()
    main()
