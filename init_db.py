"""
Run this file ONCE to create dayflow.db with empty tables.
Command:  python init_db.py
"""
import db

db.init_db()
print("Database created: dayflow.db")