from enum import Enum

class Newsletters(Enum):
    BENSBITES = ("bensbites@mail.bensbites.co", False)
    THERUNDOWN = ("news@daily.therundown.ai", True)
    TLDR = ("dan@tldrnewsletter.com", True)

    def __init__(self, email, active):
        self.email = email
        self.active = active
