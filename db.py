import sqlite3
import os
from flask import g

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dayflow.db")


def get_db():
    """
    Opens one database connection per request and reuses it.
    Flask stores it on the special 'g' object which is reset every request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["name"]
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Creates all tables from schema.sql.
    This WIPES existing data, so we only call it once, manually, to set up the database.
    """
    db = sqlite3.connect(DATABASE_PATH)
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r") as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def init_app(app):
    # Tell Flask to close the database connection automatically after each request
    app.teardown_appcontext(close_db)