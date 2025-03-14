from enum import Enum
from sqlalchemy import Enum as SqlAlchemyEnum

class BlogPostSubject(Enum):
    AI = "AI"
    BUSINESS = "BUSINESS"
    TECH = "TECH"
    HEALTH = "HEALTH"
    LIFESTYLE = "LIFESTYLE"
    FINANCE = "FINANCE"
    TRAVEL = "TRAVEL"
    EDUCATION = "EDUCATION"
    ENTERTAINMENT = "ENTERTAINMENT"
    SCIENCE = "SCIENCE"
    SPORTS = "SPORTS"

    