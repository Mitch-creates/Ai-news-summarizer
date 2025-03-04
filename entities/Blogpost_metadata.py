from dataclasses import dataclass
from datetime import datetime

@dataclass
class BlogPostMetadata:
    def __init__(self, 
                 title: str, 
                 subtitle: str, 
                 date: datetime, 
                 description: str, 
                 author: str,
                 image: str,
                 slug: str):
         self.title = title
         self.subtitle = subtitle
         self.date = date
         self.description = description
         self.author = author
         self.image = image
         self.slug = slug

    def __repr__(self):
          return f"BlogPostMetadata(title={self.title}, date={self.date}, author={self.author})"

