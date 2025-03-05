from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database.base import Base

@dataclass
class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_name = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sender_email = Column(String, nullable=False)
    gmail_id = Column(String, unique=True, nullable=False)
    published = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Email(sender_name={self.sender_name}, date={self.date}, subject={self.subject}, sender_email={self.sender_email})"
