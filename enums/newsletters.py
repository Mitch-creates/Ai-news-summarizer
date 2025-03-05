from enum import Enum as PyEnum
from sqlalchemy import Enum as SqlAlchemyEnum


class Newsletters(PyEnum):
    BENSBITES = ("bensbites@mail.bensbites.co", False)
    THERUNDOWN = ("news@daily.therundown.ai", False)
    TLDR = ("dan@tldrnewsletter.com", True)

    def __init__(self, email, active):
        self.email = email
        self.active = active
