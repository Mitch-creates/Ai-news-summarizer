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
    """Insert a new email summary into the emails table."""
    sql = '''INSERT INTO emails(sender, subject, body, summary)
             VALUES(?, ?, ?, ?)'''
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