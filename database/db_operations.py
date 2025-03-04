import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite Database connected: {db_file}")
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """Create a table for storing email objects."""
    try:
        sql_create_emails_table = """CREATE TABLE IF NOT EXISTS emails (
                                        id integer PRIMARY KEY,
                                        sender_name text NOT NULL,
                                        date text NOT NULL,
                                        subject text NOT NULL,
                                        body text NOT NULL,
                                        sender_email text NOT NULL,
                                        unique_id text NOT NULL,
                                        published integer NOT NULL
                                    );"""
        cursor = conn.cursor()
        cursor.execute(sql_create_emails_table)
    except Error as e:
        print(e)

def insert_email(conn, email):
    """Insert a new email into the emails table."""
    sql = '''INSERT INTO emails(sender_name, date, subject, body, sender_email, unique_id, published)
             VALUES(?, ?, ?, ?, ?, ?, ?)'''
    cursor = conn.cursor()
    cursor.execute(sql, email)
    conn.commit()
    return cursor.lastrowid

def update_email_published_status(conn, email_id, published):
    """Update the published status of an email."""
    sql = '''UPDATE emails
             SET published = ?
             WHERE unique_id = ?'''
    cursor = conn.cursor()
    cursor.execute(sql, (published, email_id))
    conn.commit()

def get_all_emails(conn):
    """Get all emails from the emails table."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails")
    rows = cursor.fetchall()
    return rows

def get_email_by_id(conn, email_id):
    """Get an email by its unique ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails WHERE unique_id=?", (email_id,))
    row = cursor.fetchone()
    return row

def check_if_email_exists(conn, unique_id):
    """Check if an email with the given unique ID exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails WHERE unique_id=?", (unique_id,))
    return cursor.fetchone() is not None

