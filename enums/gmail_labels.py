from enum import Enum
from sqlalchemy import Enum as SqlAlchemyEnum


class GmailLabels(Enum):
    READ = "READ"
    UNREAD = "UNREAD"
    PARSED = "PARSED"
    PUBLISHED = "PUBLISHED"