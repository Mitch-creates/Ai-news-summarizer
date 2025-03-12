from enum import Enum
from sqlalchemy import Enum as SqlAlchemyEnum

class BlogPostStatus(Enum):
   DRAFT = "DRAFT"
   PUBLISHED = "PUBLISHED"
   ARCHIVED = "ARCHIVED"
   MARKDOWN_CREATED = "MARKDOWN_CREATED"