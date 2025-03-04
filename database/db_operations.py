import sqlite3
from sqlite3 import Error
import json
from enums.blogpost_status import BlogPostStatus
from datetime import datetime
from entities.Blogpost import BlogPost
from entities.Blogpost_metadata import BlogPostMetadata

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
    """Insert a new email into the emails table and return the created email."""
    sql = '''INSERT INTO emails(sender_name, date, subject, body, sender_email, unique_id, published)
             VALUES(?, ?, ?, ?, ?, ?, ?)'''
    cursor = conn.cursor()
    cursor.execute(sql, email)
    conn.commit()
    email_id = cursor.lastrowid
    return get_email_by_id(conn, email_id)

def update_email_published_status(conn, email_id, published):
    """Update the published status of an email and return the updated email."""
    sql = '''UPDATE emails
             SET published = ?
             WHERE unique_id = ?'''
    cursor = conn.cursor()
    cursor.execute(sql, (published, email_id))
    conn.commit()
    return get_email_by_id(conn, email_id)

def get_all_emails(conn):
    """Get all emails from the emails table."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails")
    rows = cursor.fetchall()
    return rows

def get_email_by_id(conn, email_id):
    """Get an email by its unique ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails WHERE id=?", (email_id,))
    row = cursor.fetchone()
    return row

def check_if_email_exists(conn, unique_id):
    """Check if an email with the given unique ID exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails WHERE id=?", (unique_id,))
    return cursor.fetchone() is not None

def create_blogpost_table(conn):
    """Create a table for storing blog posts."""
    try:
        sql_create_blogpost_table = """CREATE TABLE IF NOT EXISTS blogposts (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        title TEXT NOT NULL,
                                        subtitle TEXT,
                                        created_at TEXT NOT NULL,
                                        published_at TEXT,
                                        content TEXT NOT NULL,
                                        email_count INTEGER NOT NULL,
                                        newsletter_sources TEXT NOT NULL,
                                        word_count INTEGER NOT NULL,
                                        openai_model TEXT NOT NULL,
                                        tokens_used INTEGER NOT NULL,
                                        markdown_file_path TEXT NOT NULL,
                                        status TEXT NOT NULL,
                                        tags TEXT NOT NULL,
                                        prompt_used TEXT NOT NULL,
                                        metadata TEXT NOT NULL
                                    );"""
        cursor = conn.cursor()
        cursor.execute(sql_create_blogpost_table)
    except Error as e:
        print(e)

def insert_blogpost(conn, blogpost):
    """Insert a new blog post into the database and return the created blog post."""
    sql = '''INSERT INTO blogposts(title, subtitle, created_at, published_at, content, 
                                   email_count, newsletter_sources, word_count, 
                                   openai_model, tokens_used, markdown_file_path, 
                                   status, tags, prompt_used, metadata)
             VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    cursor = conn.cursor()
    
    cursor.execute(sql, (
        blogpost.metadata.title,  # Use metadata title
        blogpost.metadata.subtitle,  # Use metadata subtitle
        blogpost.created_at.isoformat(),  # Convert datetime to string
        blogpost.published_at.isoformat() if blogpost.published_at else None, 
        blogpost.content, 
        blogpost.email_count, 
        json.dumps(blogpost.newsletter_sources),  # Convert list to JSON string
        blogpost.word_count, 
        blogpost.openai_model, 
        blogpost.tokens_used, 
        blogpost.markdown_file_path, 
        blogpost.status.value,  # Store enum as string
        json.dumps(blogpost.tags),  # Convert list to JSON string
        blogpost.prompt_used,
        json.dumps(blogpost.metadata.__dict__)  # Convert metadata to JSON string
    ))
    
    conn.commit()
    blogpost.id = cursor.lastrowid  # Set the generated ID to the blogpost object
    return get_blogpost_by_id(conn, blogpost.id)

def get_blogpost_by_id(conn, post_id):
    """Retrieve a blog post by ID and convert JSON fields back to Python lists."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blogposts WHERE id=?", (post_id,))
    row = cursor.fetchone()

    if row:
        metadata_dict = json.loads(row[14])  # Convert JSON string back to dict
        metadata = BlogPostMetadata(**metadata_dict)  # Create BlogPostMetadata object

        return BlogPost(
            created_at=datetime.fromisoformat(row[3]),
            published_at=datetime.fromisoformat(row[4]) if row[4] else None,
            content=row[5],
            email_count=row[6],
            newsletter_sources=json.loads(row[7]),  # Convert JSON string back to list
            word_count=row[8],
            openai_model=row[9],
            tokens_used=row[10],
            markdown_file_path=row[11],
            status=BlogPostStatus(row[12]),  # Convert string back to Enum
            tags=json.loads(row[13]),  # Convert JSON string back to list
            prompt_used=row[14],
            metadata=metadata  # Use the BlogPostMetadata object
        )
    
    return None

def update_blogpost_status(conn, post_id, new_status):
    """Update the status of a blog post and return the updated blog post."""
    sql = '''UPDATE blogposts SET status = ? WHERE id = ?'''
    cursor = conn.cursor()
    cursor.execute(sql, (new_status.value, post_id))  # Store enum as string
    conn.commit()
    return get_blogpost_by_id(conn, post_id)

def create_blogpost_metadata_table(conn):
    """Create a table for storing blog post metadata."""
    try:
        sql_create_blogpost_metadata_table = """CREATE TABLE IF NOT EXISTS blogpost_metadata (
                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                title TEXT NOT NULL,
                                                subtitle TEXT,
                                                date TEXT NOT NULL,
                                                description TEXT NOT NULL,
                                                author TEXT NOT NULL,
                                                image TEXT NOT NULL,
                                                slug TEXT NOT NULL
                                            );"""
        cursor = conn.cursor()
        cursor.execute(sql_create_blogpost_metadata_table)
    except Error as e:
        print(e)

def insert_blogpost_metadata(conn, metadata):
    """Insert a new blog post metadata into the database and return the created metadata."""
    sql = '''INSERT INTO blogpost_metadata(title, subtitle, date, description, author, image, slug)
             VALUES(?, ?, ?, ?, ?, ?, ?)'''
    cursor = conn.cursor()
    cursor.execute(sql, (
        metadata.title,
        metadata.subtitle,
        metadata.date.isoformat(),  # Convert datetime to string
        metadata.description,
        metadata.author,
        metadata.image,
        metadata.slug
    ))
    conn.commit()
    metadata.id = cursor.lastrowid  # Set the generated ID to the metadata object
    return get_blogpost_metadata_by_id(conn, metadata.id)

def get_blogpost_metadata_by_id(conn, metadata_id):
    """Retrieve blog post metadata by ID and convert JSON fields back to Python lists."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blogpost_metadata WHERE id=?", (metadata_id,))
    row = cursor.fetchone()

    if row:
        return BlogPostMetadata(
            title=row[1],
            subtitle=row[2],
            date=datetime.fromisoformat(row[3]),  # Convert string back to datetime
            description=row[4],
            author=row[5],
            image=row[6],
            slug=row[7]
        )
    
    return None

def update_blogpost_metadata(conn, metadata_id, metadata):
    """Update an existing blog post metadata and return the updated metadata."""
    sql = '''UPDATE blogpost_metadata
             SET title = ?, subtitle = ?, date = ?, description = ?, author = ?, image = ?, slug = ?
             WHERE id = ?'''
    cursor = conn.cursor()
    cursor.execute(sql, (
        metadata.title,
        metadata.subtitle,
        metadata.date.isoformat(),  # Convert datetime to string
        metadata.description,
        metadata.author,
        metadata.image,
        metadata.slug,
        metadata_id
    ))
    conn.commit()
    return get_blogpost_metadata_by_id(conn, metadata_id)
