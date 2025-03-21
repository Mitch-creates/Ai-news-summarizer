from enum import Enum as PyEnum
from sqlalchemy import Enum as SqlAlchemyEnum

from enums.blogpost_subject import BlogPostSubject


class Newsletters(PyEnum):
    BENSBITES = ("bensbites@mail.bensbites.co", False, BlogPostSubject.AI)
    THERUNDOWN = ("news@daily.therundown.ai", True, BlogPostSubject.AI)
    TLDR = ("dan@tldrnewsletter.com", True, BlogPostSubject.AI)
    TECHCRUNCH = ('newsletters@techcrunch.com', True, BlogPostSubject.TECH)
    THEDOWNLOAD = ('newsletters@technologyreview.com', True, BlogPostSubject.TECH)


    def __init__(self, email, active, subject: BlogPostSubject):
        self._email = email
        self._active = bool(active)
        self._subject = subject

    @property
    def email(self):
        return self.value[0]

    @property
    def active(self):
        return bool(self.value[1])

    @property
    def subject(self):
        return self.value[2]