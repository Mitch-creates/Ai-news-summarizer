from dataclasses import dataclass
import json
from typing import Optional, List
from datetime import datetime

from enums.blogpost_status import BlogPostStatus

@dataclass
class BlogPostMetadataDTO:
    id: Optional[int]
    title: str
    date: Optional[datetime]
    description: Optional[str]
    author: Optional[str]
    image: Optional[str]
    slug: Optional[str]

    @staticmethod
    def from_orm(metadata) -> "BlogPostMetadataDTO":
        return BlogPostMetadataDTO(
            id=metadata.id,
            title=metadata.title,
            date=metadata.date,
            description=metadata.description,
            author=metadata.author,
            image=metadata.image,
            slug=metadata.slug,
        )

    def to_orm(self):
        from entities.Blogpost_metadata import BlogPostMetadata  # Avoid circular import
        return BlogPostMetadata(
            id=self.id,
            title=self.title,
            date=self.date,
            description=self.description,
            author=self.author,
            image=self.image,
            slug=self.slug,
        )

@dataclass
class BlogPostDTO:
    id: int
    created_at: Optional[datetime]
    published_at: Optional[datetime]
    content: str
    email_count: int
    newsletter_sources: List[str]
    word_count: int
    openai_model: str
    tokens_used: int
    markdown_file_path: Optional[str]
    status: str
    tags: List[str]
    prompt_used: Optional[str]
    blogpost_metadata: Optional[BlogPostMetadataDTO] = None  # Default to None

    @staticmethod
    def from_orm(blogpost) -> "BlogPostDTO":
        """Converts a SQLAlchemy BlogPost instance into a BlogPostDTO."""
        print(f"Michiel{type(blogpost.newsletter_sources)}")
        return BlogPostDTO(
            id=blogpost.id,
            created_at=blogpost.created_at,
            published_at=blogpost.published_at,
            content=blogpost.content,
            email_count=blogpost.email_count,
            newsletter_sources=json.loads(blogpost.newsletter_sources) if blogpost.newsletter_sources else [],
            word_count=blogpost.word_count,
            openai_model=blogpost.openai_model,
            tokens_used=blogpost.tokens_used,
            markdown_file_path=blogpost.markdown_file_path,
            status=blogpost.status.value,  # Assuming BlogPostStatus is an Enum
            tags=json.loads(blogpost.tags) if blogpost.tags else [],
            prompt_used=blogpost.prompt_used,
            blogpost_metadata=BlogPostMetadataDTO.from_orm(blogpost.blogpost_metadata) if blogpost.blogpost_metadata else None
        )

    def to_orm(self):
        from entities.Blogpost import BlogPost  # Avoid circular dependency
        blogpost = BlogPost(
            id=self.id,
            created_at=self.created_at,
            published_at=self.published_at,
            content=self.content,
            email_count=self.email_count,
            newsletter_sources=json.dumps(self.newsletter_sources),
            word_count=self.word_count,
            openai_model=self.openai_model,
            tokens_used=self.tokens_used,
            markdown_file_path=self.markdown_file_path,
            status=BlogPostStatus(self.status),  # If this is an enum, you'll need to convert appropriately
            tags=json.dumps(self.tags),
            prompt_used=self.prompt_used,
        )
        if self.blogpost_metadata:
            blogpost.blogpost_metadata = self.blogpost_metadata.to_orm()
        return blogpost
