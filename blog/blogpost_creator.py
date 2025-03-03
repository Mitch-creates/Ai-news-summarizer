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

def create_blogpost(body):
    """Summarizes the email body using OpenAI's GPT-3.5 model."""
    prompt = f"The following is a String of gathered newsletter bodies from AI news companies seperated by hashtags. First of all it's important to analyze them seperately and ignore the ones that are clearly an advertisement and have no value. You are a blogpost writer and care most about the readability and engaging elements of your posts. The idea is to summarize and share the news around AI of the last week starting with a short, fun intro about yourself and the news you're going to talk about in this blogpost. The whole idea of this blogpost is that it's really special because it's written by AI, about AI:\n\n{body}"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=100
        )
        blogpost = response.choices[0].message.content.strip()
        return blogpost
    except Exception as e:
        print(f"Error in generating blogpost: {e}")
        return "Failed to generate blogpost"
