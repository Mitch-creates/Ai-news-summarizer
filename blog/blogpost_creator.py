import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/environment_variables.env")

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if api_key is None:
    raise ValueError("Error: OPENAI_API_KEY is not set in the environment variables.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

model = "gpt-3.5-turbo"

def create_blogpost(emails: list) -> str:
    """Summarizes the email body using OpenAI's GPT-3.5 model."""
    body = format_email_body_for_openai(emails)

    prompt = (
        f"You are an AI-powered blog writer specializing in AI news. Below is a collection of AI-related newsletters from the past week.\n\n"
        f"### Task:\n"
        f"1. **Analyze each newsletter separately** and **ignore any that are purely advertisements** or have no valuable news.\n"
        f"2. **Extract key insights** from the remaining newsletters and merge them into a structured, engaging, and easy-to-read blog post.\n"
        f"3. Start the blog post with a **short, fun, and engaging introduction** about yourself and the AI news you'll cover.\n"
        f"4. Ensure the post feels **natural, well-written, and compelling**—like a high-quality human-written blog.\n\n"
        f"### Guidelines:\n"
        f"- Focus on **readability** and an engaging **storytelling approach**.\n"
        f"- Maintain a **conversational yet informative tone**.\n"
        f"- Highlight **the most important AI developments** in a structured format.\n"
        f"- Make the post **flow naturally** instead of just summarizing bullet points.\n"
        f"- If possible, include an insightful closing statement or takeaway.\n\n"
        f"### Metadata:\n"
        f"Please also generate the following metadata for the blog post:\n"
        f"- **title**: \"Weekly AI News Summary\"\n"
        f"- **subtitle**: A short, engaging one-liner summarizing the blog post (e.g., \"The biggest AI breakthroughs this week!\")\n"
        f"- **date**: Use today’s date\n"
        f"- **author**: \"AI\"\n"
        f"- **image**: Leave blank\n"
        f"- **slug**: \"ai-news\"\n"
        f"- **description**: A concise, engaging summary of the blog post (2-3 sentences).\n\n"
        f"### Newsletters:\n"
        f"{body}"
    )

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=1000
        )
        blogpost = response.choices[0].message.content.strip()
        return blogpost
    except Exception as e:
        print(f"Error in generating blogpost: {e}")
        return "Failed to generate blogpost"
    
def format_email_body_for_openai(emails: list) -> str:
    """Takes the needed data and structures it for OpenAI processing."""
    
    if not emails:
        return "No emails available for processing."
    
    structured_bodies = []

    for email in emails:
        structured_body = (
            f"Newsletter: {email.sender_name}\n"
            f"Email: {email.sender_email}\n"
            f"Subject: {email.subject}\n"
            f"Date: {email.date}\n\n"
            f"Content:\n{email.body}\n\n"
            f"{'-' * 30}"
        )
        structured_bodies.append(structured_body)

    return "\n".join(structured_bodies)
