from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="environment_variables.env")

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if api_key is None:
    raise ValueError("Error: OPENAI_API_KEY is not set in the environment variables.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

model = "gpt-3.5-turbo"

def summarize_email(body):
    """Summarizes the email body using OpenAI's GPT-3.5 model."""
    prompt = f"Summarize the following email:\n\n{body}"
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=100
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error in summarizing email: {e}")
        return "Failed to summarize"
