from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import JSON, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from database.base import Base


@dataclass
class BlogPostMetadata(Base):
    __tablename__ = 'blog_post_metadata'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    title: str = Column(String, nullable=False)
    date: datetime = Column(DateTime, nullable=False)
    description: str = Column(JSON, nullable=False)
    author: str = Column(String, nullable=False)
    image: str = Column(String)
    slug: str = Column(String)

    # Back reference to BlogPost
    blogposts = relationship('BlogPost', back_populates='blogpost_metadata')