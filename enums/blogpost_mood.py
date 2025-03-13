from enum import Enum

class BlogPostMood(Enum):
    PROFESSIONAL = (
        "professional",
        "Write in a professional, informative style suitable for a knowledgeable audience. "
        "Focus on clarity, accuracy, and an objective tone.",
        
    )
    HUMOROUS = (
        "humorous",
        "Write in an entertaining, playful, and engaging style with witty remarks and humor."
    )
    SKEPTICAL = (
        "skeptical",
        "Write in a skeptical, critical tone. Question claims, highlight potential hype, "
        "and maintain a slightly doubtful perspective."
    )
    OPTIMISTIC = (
        "optimistic",
        "Write with an enthusiastic, positive, and optimistic tone. Highlight opportunities "
        "and positive aspects of AI developments."
    )
    INFORMAL = (
        "informal",
        "Write casually and conversationally, as if chatting with a friend. Keep it relatable "
        "and easygoing, without losing clarity."
    )

    def __init__(self, mood_name, instruction):
        self.mood_name = mood_name
        self.instruction = instruction

    def __str__(self):
        return self.mood_name