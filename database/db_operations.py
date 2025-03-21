from contextlib import contextmanager
import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, joinedload, object_session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from enums.blogpost_status import BlogPostStatus
from enums.gmail_labels import GmailLabels
from enums.newsletters import Newsletters
from datetime import datetime
import re
from entities.Email import Email
from entities.Blogpost import BlogPost
from entities.Blogpost_metadata import BlogPostMetadata
from entities.BlogpostDTO import BlogPostDTO, BlogPostMetadataDTO
import logging
from database.base import Base

# Enable logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # Show SQL queries
logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)  # Show additional debug info

load_dotenv("config/environment_variables.env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

@contextmanager
def get_session():
    """Context manager for SQLAlchemy session."""
    session = Session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def initialize_database():
    """Initialize the database with the required tables."""
    try:
        # Print the names of the tables to see if the table exists in metadata
        Base.metadata.create_all(engine)  # Create all tables
        print("Tables created successfully.")
        
        # Check again to confirm
        print("Tables after creation:", Base.metadata.tables.keys())

    except SQLAlchemyError as e:
        print(f"Error creating database tables: {e}")

def insert_email(email):
    """Insert a new email into the emails table and return the created email."""

    if isinstance(email.date, str):
        email.date = convert_date(email.date)

    with get_session() as session:
        session.add(email)
        session.commit()
        session.refresh(email)
    return email

def update_email_published_status(email_id, published):
    """Update the published status of an email and return the updated email."""
    with get_session() as session:
        email = session.query(Email).filter(Email.id == email_id).first()
        if email:
            email.published = published
            session.commit()
            session.refresh(email)
    return email

def get_all_emails():
    """Get all emails from the emails table."""
    with get_session() as session:
        emails = session.query(Email).all()
    return emails

def get_email_by_id(email_id):
    """Get an email by its unique ID."""
    with get_session() as session:
        email = session.query(Email).filter(Email.id == email_id).first()
    return email

def check_if_email_exists_by_gmail_id(gmail_id):
    """Check if an email with the given unique Gmail ID exists in the database."""
    with get_session() as session:
        exists = session.query(Email).filter(Email.gmail_id == gmail_id).first() is not None
    return exists

def insert_blogpost(blogpost, slug):
    """Insert a new blog post into the database and return the created blog post."""

    if isinstance(blogpost.published_at, str):
        blogpost.published_at = convert_date(blogpost.published_at)

    if isinstance(blogpost.created_at, str):
        blogpost.created_at = convert_date(blogpost.created_at)

    if isinstance(blogpost.newsletter_sources, list):
        blogpost.newsletter_sources = json.dumps(blogpost.newsletter_sources)  # Convert list to JSON string

    if isinstance(blogpost.tags, list):
        blogpost.tags = json.dumps(blogpost.tags)
    
    with get_session() as session:
        session.add(blogpost)
        session.commit()
        session.refresh(blogpost)

        if blogpost.blogpost_metadata:
            _ = blogpost.blogpost_metadata
            session.refresh(blogpost.blogpost_metadata)

        if blogpost.blogpost_metadata and not blogpost.blogpost_metadata.slug:
            blogpost.blogpost_metadata.slug = slug
            session.commit()
            session.refresh(blogpost.blogpost_metadata)

    return BlogPostDTO.from_orm(blogpost)

def get_blogpost_by_id(post_id):
    """Retrieve a blog post and its metadata using metadata_id."""
    with get_session() as session:
        blogpost = session.query(BlogPost).options(joinedload(BlogPost.blogpost_metadata)).filter(BlogPost.id == post_id).first()
        
        if blogpost:
            # Optionally force loading:
            _ = blogpost.blogpost_metadata
            
    return BlogPostDTO.from_orm(blogpost)

def update_blogpost_status(post_id, new_status):
    """Update the status of a blog post and return the updated blog post."""
    with get_session() as session:
        blogpost = session.query(BlogPost).filter(BlogPost.id == post_id).first()
        if blogpost:
            blogpost.status = new_status
            session.commit()
            session.refresh(blogpost)


    return BlogPostDTO.from_orm(blogpost)

def update_blogpost(post_id, blogpost):
    """Update an existing blog post and return the updated blog post."""
    with get_session() as session:
        existing_blogpost = session.query(BlogPost).options(
            joinedload(BlogPost.blogpost_metadata)
        ).filter(BlogPost.id == post_id).first()

        if hasattr(blogpost, 'blogpost_metadata') and blogpost.blogpost_metadata:
            if existing_blogpost.blogpost_metadata:
                # Update the existing `blogpost_metadata` fields instead of replacing the object
                existing_blogpost.blogpost_metadata.title = blogpost.blogpost_metadata.title
                existing_blogpost.blogpost_metadata.slug = blogpost.blogpost_metadata.slug
                existing_blogpost.blogpost_metadata.date = blogpost.blogpost_metadata.date
                existing_blogpost.blogpost_metadata.description = blogpost.blogpost_metadata.description
                existing_blogpost.blogpost_metadata.author = blogpost.blogpost_metadata.author
                existing_blogpost.blogpost_metadata.image = blogpost.blogpost_metadata.image

                session.merge(existing_blogpost.blogpost_metadata)
            else:
                # If no metadata exists, assign the new metadata (this should happen only once)
                existing_blogpost.blogpost_metadata = session.merge(blogpost.blogpost_metadata)

        # Iterate over the DTO's dictionary and update scalar fields
        for key, value in vars(blogpost).items():
            if key == 'blogpost_metadata':
                continue
            if key == 'newsletter_sources' and isinstance(value, list):
                value = json.dumps(value)  # Convert list to JSON string
            if key == 'tags' and isinstance(value, list):
                value = json.dumps(value)  # Convert list to JSON string
            if key in ['created_at', 'published_at'] and isinstance(value, str):
                value = convert_date(value)  # Convert string to datetime
            setattr(existing_blogpost, key, value)
        
        # Debug before merging the blogpost
        blogpost_before = id(existing_blogpost)
        
        # Reattach the blogpost using merge
        merged_blogpost = session.merge(existing_blogpost)
        
        session.commit()
        session.refresh(merged_blogpost)
        
        updated_dto = BlogPostDTO.from_orm(merged_blogpost)
        return updated_dto

def insert_blogpost_metadata(metadata):
    """Insert a new blog post metadata into the database and return the created metadata."""

    if isinstance(metadata.date, str):
        metadata.date = convert_date(metadata.date)
    
    with get_session() as session:
        session.add(metadata)
        session.commit()
        session.refresh(metadata)
    return BlogPostMetadataDTO.from_orm(metadata)

def get_blogpost_metadata_by_id(metadata_id):
    """Retrieve blog post metadata by ID and convert JSON fields back to Python lists."""
    with get_session() as session:
        metadata = session.query(BlogPostMetadata).filter(BlogPostMetadata.id == metadata_id).first()
        # if metadata:
            # metadata.date = metadata.date.isoformat() if metadata.date else None
    return BlogPostMetadataDTO.from_orm(metadata)

def update_blogpost_metadata(metadata_id, metadata):
    """Update an existing blog post metadata and return updated metadata."""
    with get_session() as session:
        existing_metadata = session.query(BlogPostMetadata).filter(BlogPostMetadata.id == metadata_id).first()
        if existing_metadata:
            for key, value in metadata.__dict__.items():
                if key == 'date' and isinstance(value, str):
                    value = convert_date(value)  # Convert string to datetime
                setattr(existing_metadata, key, value)
            session.commit()
            session.refresh(existing_metadata)
            # existing_metadata.date = existing_metadata.date.isoformat() if existing_metadata.date else None
    return BlogPostMetadataDTO.from_orm(existing_metadata)
    
def convert_date(date_str):
    # Extract the main date-time part (before optional "(UTC)" or other extras)
    match = re.match(r"^(.*?\+\d{4})", date_str)
    if match:
        clean_date_str = match.group(1)
        return datetime.strptime(clean_date_str, "%a, %d %b %Y %H:%M:%S +0000")
    
    raise ValueError(f"Invalid date format: {date_str}")

