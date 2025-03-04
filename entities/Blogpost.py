from typing import List, Optional
from datetime import datetime
from enums.blogpost_status import BlogPostStatus

class BlogPost:
    def __init__(self, 
                 title: str, 
                 subtitle: str, 
                 created_at: datetime, 
                 published_at: Optional[datetime], 
                 content: str, 
                 email_count: int, 
                 newsletter_sources: List[str], 
                 word_count: int, 
                 openai_model: str, 
                 tokens_used: int, 
                 markdown_file_path: str, 
                 status: BlogPostStatus, 
                 tags: List[str]):
        self.title = title  # str
        self.subtitle = subtitle  # str
        self.created_at = created_at  # datetime
        self.published_at = published_at  # datetime or None if not published yet
        self.content = content  # str (Full blog post)
        self.email_count = email_count  # int (Number of emails used)
        self.newsletter_sources = newsletter_sources  # List[str] (List of newsletter names)
        self.word_count = word_count  # int (Word count of the post)
        self.openai_model = openai_model  # str (e.g., "gpt-3.5-turbo")
        self.tokens_used = tokens_used  # int (Total tokens used in API call)
        self.markdown_file_path = markdown_file_path  # str (Path to saved .md file)
        self.status = status  # Enum (e.g., "draft", "published", "archived")
        self.tags = tags  # List[str] (For metadata and organization)

    def __repr__(self):
        return f"BlogPost(title={self.title}, created_at={self.created_at}, status={self.status}, email_count={self.email_count})"
