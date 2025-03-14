from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from entities.Blogpost_metadata import BlogPostMetadata
from sqlalchemy.ext.declarative import declarative_base
from enums.blogpost_status import BlogPostStatus
from sqlalchemy import Enum as SqlAlchemyEnum
from database.base import Base
from enums.blogpost_subject import BlogPostSubject

@dataclass
class BlogPost(Base):
    __tablename__ = 'blogposts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    content = Column(Text, nullable=False)
    email_count = Column(Integer, nullable=False)
    newsletter_sources = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    openai_model = Column(String, nullable=False)
    tokens_used = Column(Integer, nullable=False)
    markdown_file_path = Column(String)
    status = Column(SqlAlchemyEnum(BlogPostStatus, name="blogpost_status"), nullable=False)  # ForeignKey to your Enum table (assuming it's stored in DB)
    tags = Column(String)  # Storing list as an array (use PostgreSQL)
    prompt_used = Column(String)
    blogpost_subject = Column(SqlAlchemyEnum(BlogPostSubject, name="blogpost_subject"), nullable=False)  # ForeignKey to your Enum table (assuming it's stored in DB)
    blogpost_metadata_id = Column(Integer, ForeignKey('blog_post_metadata.id'))  # ForeignKey to BlogPostMetadata

    # Relationship with BlogPostMetadata
    blogpost_metadata = relationship("BlogPostMetadata", back_populates="blogposts", lazy='selectin')


       