import time
import json
import subprocess
import openai
import os
from dotenv import load_dotenv
import yaml
from bs4 import BeautifulSoup
import requests
from datetime import datetime

from entities.Blogpost import BlogPost
from entities.BlogpostDTO import BlogPostDTO
from entities.Blogpost_metadata import BlogPostMetadata
from enums.blogpost_status import BlogPostStatus
import database.db_operations

# Load environment variables
load_dotenv("config/environment_variables.env")

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if api_key is None:
    raise ValueError("Error: OPENAI_API_KEY is not set in the environment variables.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

model = os.getenv("OPENAI_MODEL")

# Custom YAML dumper to prevent quotes around dates and add quotes for special strings
class NoQuotesForDatesDumper(yaml.SafeDumper):
    def represent_str(self, data):
        """Ensure strings are wrapped in double quotes only when needed."""
        if ":" in data or "\n" in data or any(c in data for c in ['#', '-', '{', '}']):
            # Add quotes around strings containing colons, newlines or other special chars
            return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')
        # Otherwise, no quotes for simple strings
        return self.represent_scalar('tag:yaml.org,2002:str', data)

    def represent_datetime(self, data):
        """Ensure dates are written in YYYY-MM-DD format without quotes."""
        return self.represent_scalar('tag:yaml.org,2002:timestamp', data.strftime("%Y-%m-%d"))
    
def create_blogpost(emails: list) -> BlogPostDTO:
    """Summarizes the email body using OpenAI's GPT-3.5 model."""
    body = format_email_body_for_openai(emails)

    # prompt = (
    #     f"You are an AI-powered blog writer specializing in AI news. Below is a collection of AI-related newsletters from the past week.\n\n"
    #     f"### Task:\n"
    #     f"1. **Analyze each newsletter separately** and **ignore any that are purely advertisements** or have no valuable news.\n"
    #     f"2. **Extract key insights** from the remaining newsletters and merge them into a structured, engaging, and easy-to-read blog post.\n"
    #     f"3. Start the blog post with a **short, fun, and engaging introduction** about yourself and the AI news you'll cover.\n"
    #     f"4. Ensure the post feels **natural, well-written, and compelling**—like a high-quality human-written blog.\n\n"
    #     f"### Guidelines:\n"
    #     f"- Focus on **readability** and an engaging **storytelling approach**.\n"
    #     f"- Maintain a **conversational yet informative tone**.\n"
    #     f"- Highlight **the most important AI developments** in a structured format.\n"
    #     f"- Make the post **flow naturally** instead of just summarizing bullet points.\n"
    #     f"- If possible, include an insightful closing statement or takeaway.\n\n"
    #     f"### Metadata:\n"
    #     f"Please also generate the following metadata for the blog post:\n"
    #     f"- **title**: \"Weekly AI News Summary\"\n"
    #     f"- **subtitle**: A short, engaging one-liner summarizing the blog post (e.g., \"The biggest AI breakthroughs this week!\")\n"
    #     f"- **date**: Use today’s date\n"
    #     f"- **author**: \"AI\"\n"
    #     f"- **image**: Leave blank\n"
    #     f"- **slug**: \"ai-news\"\n"
    #     f"- **description**: A concise, engaging summary of the blog post (2-3 sentences).\n\n"
    #     f"### Newsletters:\n"
    #     f"{body}"
    # )

    # prompt = (f"You are an AI-powered blog writer specializing in AI news. Below is a collection of AI-related newsletters from the past week.\n\n"
    # f"### Task:\n"
    # f"1. **Analyze each newsletter separately** and **ignore any that are purely advertisements** or have no valuable news.\n"
    # f"2. **Extract key insights** from the remaining newsletters and merge them into a structured, engaging, and easy-to-read blog post.\n"
    # f"3. Start the blog post with a **short, fun, and engaging introduction** about yourself and the AI news you'll cover.\n"
    # f"4. Ensure the post feels **natural, well-written, and compelling**—like a high-quality human-written blog.\n\n"
    # f"### Guidelines:\n"
    # f"- Focus on **readability** and an engaging **storytelling approach**.\n"
    # f"- Maintain a **conversational yet informative tone**.\n"
    # f"- Highlight **the most important AI developments** in a structured format.\n"
    # f"- Make the post **flow naturally** instead of just summarizing bullet points.\n"
    # f"- If possible, include an insightful closing statement or takeaway.\n\n"
    # f"### Response Format:\n"
    # f"Generate the response as a structured YAML document with the following format:\n"
    # f"```yaml\n"
    # f"subtitle: \"A short, engaging one-liner summarizing the blog post\"\n"
    # f"description: \"A concise, engaging summary of the blog post (2-3 sentences)\"\n"
    # f"content: |\n"
    # f"  <h1>Weekly AI News Summary</h1>\n"
    # f"  \n"
    # f"  <h2>[Subtitle Here]</h2>\n"
    # f"  \n"
    # f"  <p>[Introduction]</p>\n"
    # f"  \n"
    # f"  <h2>[Subheading]</h2>\n"
    # f"  <p>[Paragraph about AI news]</p>\n"
    # f"  \n"
    # f"  <h2>[Another Subheading]</h2>\n"
    # f"  <p>[More AI news]</p>\n"
    # f"  \n"
    # f"  <p>[Closing statement]</p>\n"
    # f"```\n"
    # f"Ensure the `content` field contains properly formatted HTML elements, including `<h1>`, `<h2>`, and `<p>`, without bullet points unless necessary.\n\n"
    # f"{body}"
    # )

    prompt = (f"You are an AI-powered blog writer specializing in AI news. Below is a collection of AI-related newsletters from the past week.\n\n"
    f"### Task:\n"
    f"1. **Analyze each newsletter separately** and **ignore any that are purely advertisements** or have no valuable news (yes, the ones full of buzzwords and no substance).\n"
    f"2. **Extract key insights** from the remaining newsletters and merge them into a structured, engaging, and easy-to-read blog post.\n"
    f"3. Start the blog post with a **short, fun, and sarcastic introduction** where you subtly question the hype around AI news (you know, the 'what’s new this week?' vibe).\n"
    f"4. Ensure the post feels **natural, well-written, and compelling**—like a high-quality human-written blog, with a touch of skepticism about the latest AI innovations.\n\n"
    f"### Guidelines:\n"
    f"- Focus on **readability** and an engaging **storytelling approach**. Don't just regurgitate what’s in the newsletters, make it *worth reading*.\n"
    f"- Maintain a **conversational yet informative tone**, with a sprinkle of **dark humor**—think of yourself as the AI equivalent of a skeptical, slightly jaded tech reviewer.\n"
    f"- **Skepticism is key**: Question new developments, make sarcastic remarks about *'game-changing'* claims, and call out the obvious hype surrounding AI projects.\n"
    f"- Highlight **the most important AI developments** in a structured format, but avoid sounding like a marketing brochure.\n"
    f"- Make the post **flow naturally** instead of just summarizing bullet points. Don't make it feel like a boring corporate memo.\n"
    f"- If possible, include an **insightful closing statement or takeaway**, but keep it snarky and reflective—nothing too warm and fuzzy.\n\n"
    f"### Response Format:\n"
    f"Generate the response as a structured YAML document with the following format:\n"
    f"description: \"A concise, engaging summary of the blog post (2-3 sentences) with a touch of dark humor or sarcasm about AI trends\"\n"
    f"content: |\n"
    f"  <h2>[Subheading]</h2>\n"
    f"  \n"
    f"  <p>[Introduction]</p>\n"
    f"  <p>Here's the latest in AI: *new* breakthroughs, *exciting* advancements, and *game-changing* products. Or at least that’s what the press releases say. Let's dive in, shall we?</p>\n"
    f"  \n"
    f"  <h2>[Subheading]</h2>\n"
    f"  <p>[Paragraph about AI news, add skeptical comments like 'And of course, they’re promising it’s the next big thing… who’s surprised?']</p>\n"
    f"  \n"
    f"  <h2>[Another Subheading]</h2>\n"
    f"  <p>[More AI news, with sarcastic remarks like 'Is this another AI tool that will change the world? Probably not. But let's pretend it will.']</p>\n"
    f"  \n"
    f"  <p>[Another AI news piece, as many as needed. Feel free to add as many sections as necessary for the volume of news. Each piece of news should get its own heading and paragraph.]</p>\n"
    f"  \n"
    f"  <p>[Closing statement] - [Something like: 'Will any of this actually make a real difference? Time will tell. But don’t hold your breath.']</p>\n"
    f"Ensure the `content` field contains properly formatted HTML elements, including `<h1>`, `<h2>`, and `<p>`, without bullet points unless necessary.\n\n"
    f"{body}"
)



    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=1000
        )
        response_with_backticks = response.choices[0].message.content

        if not isinstance(response_with_backticks, str):
            raise ValueError("Response is not a valid string.")
        
        response_with_backticks = response_with_backticks.strip()
        cleaned_response = response_with_backticks.strip('```yaml').strip('```')
        # TODO Running into an issue with ´´´yaml, the response starts and ends with ´´´ . Which causes an error when parsing the YAML, but we need this for our markdown file. So we need to remove it before parsing and later add it back when creating our markdown file
        blogpost = create_blogpost_instance_from_yaml(cleaned_response, prompt, len(emails), response.usage.total_tokens, [email.sender_name for email in emails])
        
        
        newly_created_blogpost = database.db_operations.insert_blogpost(blogpost)
        
        return newly_created_blogpost
    except GeneratorExit:
        print("Generator was forcefully closed.")
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

def parse_yaml_response(response: str):
    """Parses YAML response into a Python dictionary."""
    try:
        parsed_data = yaml.safe_load(response)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML response: {e}")
    return parsed_data

def create_blogpost_instance_from_yaml(response: str, prompt: str, amount_of_emails: int, amount_of_tokens: int, newsletter_sources: list) -> BlogPost:
    """Creates a BlogPost instance from the parsed YAML response."""
    parsed_data = parse_yaml_response(response)

    # Validate required fields
    required_fields = ["description", "content"]
    for field in required_fields:
        if field not in parsed_data:
            raise ValueError(f"Missing required field in response: {field}")

    metadata = BlogPostMetadata(
        title=f"{os.getenv('WEEKLY_AI_TITLE')} - Week {datetime.now().isocalendar()[1]}",
        date=datetime.now(),
        description=parsed_data["description"],
        author="AI",
        image="img/backgroundLaos.jpg",  # TODO Add image later, figure out if we wanna use AI-generated images
        slug=None
    )
    
    blogpost = BlogPost(
        created_at=datetime.now(),
        published_at=None,
        content=parsed_data["content"],
        email_count=amount_of_emails, 
        newsletter_sources=json.dumps(newsletter_sources), 
        word_count=len(remove_html_elements(parsed_data["content"])), 
        openai_model=model,
        tokens_used=amount_of_tokens, 
        markdown_file_path=None,
        status=BlogPostStatus.DRAFT,
        tags=[],
        prompt_used=prompt,
        blogpost_metadata=metadata
    )

    return blogpost

def remove_html_elements(html_content: str) -> str:
    """Removes HTML elements from the content to count the amount of words used for the blogpost."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def generate_markdown_file(blogpostDTO: BlogPostDTO) -> BlogPostDTO:
    """Generate a markdown file from a Blogpost object"""
    try:
        # Get the current directory of the script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        REPO_NAME = os.getenv("REPO_NAME")
        # Construct the relative path to the target directory
        target_dir = os.path.join(current_dir, f'../../{REPO_NAME}/content/posts')
        target_dir = os.path.abspath(target_dir)  # Ensure absolute path

        # Define filename
        slug = blogpostDTO.blogpost_metadata.slug
        filename = f"{slug}.md"
        filepath = os.path.join(target_dir, filename)

        # Create front matter (YAML metadata)
        front_matter = {
            "layout": "post",
            "title": format_front_matter_value(blogpostDTO.blogpost_metadata.title),
            "date": format_front_matter_value(blogpostDTO.blogpost_metadata.date),
            "author": format_front_matter_value(blogpostDTO.blogpost_metadata.author),
            "image": format_front_matter_value(blogpostDTO.blogpost_metadata.image),
            "slug": format_front_matter_value(blogpostDTO.blogpost_metadata.slug),
            "description": format_front_matter_value(blogpostDTO.blogpost_metadata.description)
        }
        NoQuotesForDatesDumper.add_representer(str, NoQuotesForDatesDumper.represent_str)
        NoQuotesForDatesDumper.add_representer(datetime, NoQuotesForDatesDumper.represent_datetime)

        
        # Convert front matter to YAML format, width=float('inf') ensures no line breaks
        front_matter_yaml = yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True, width=float('inf'), Dumper=NoQuotesForDatesDumper)

        # Write Markdown file
        with open(filepath, "w", encoding="utf-8") as file:
            file.write("---\n")
            file.write(front_matter_yaml)
            file.write("---\n\n")
            file.write(blogpostDTO.content)

        # Update the file path in the BlogPostDTO object
        blogpostDTO.markdown_file_path = filepath
        # Update the status of the blogpost to be MARKDOWN-CREATED
        blogpostDTO.status = BlogPostStatus.MARKDOWN_CREATED

        return blogpostDTO
    except Exception as e:
        print(f"An error occurred during the generation of the markdown file: {e}")
        return None

def format_front_matter_value(value):
    """
    Formats values for YAML front matter:
    - Dates are converted to 'YYYY-MM-DD' format.
    - Strings are enclosed in double quotes, but avoids double-wrapping.
    - Lists are converted to YAML-compatible strings.
    - None values become empty strings.
    """
    
    if isinstance(value, datetime):
        # Ensure the date is formatted correctly: YYYY-MM-DD

        return value
    elif isinstance(value, str):
        # Preserve original single quotes, only wrap in double quotes if needed
        # if ":" in value or "\n" in value:  
        #     return f'"{value}"'  # Wrap if contains colons or newlines
        return value  # Otherwise, return as-is
    elif isinstance(value, list):
        return value  # Let PyYAML handle lists correctly
    elif value is None:
        return ""  # Handle None values as empty string
    return value  

# TODO Analyse OpenAI's response if it contains everything we need for the blog post
# TODO If it does, we can proceed to save it in the database
# TODO If not, we need to refine the prompt or the processing of the emails
# TODO We can also add more metadata to the prompt to guide the AI better
# We need the following elements in the response to proceed to create the markdown file:
#---
#layout: post
#title: "Title"
#subtitle: "Subtitle"
#date: 2024-01-09
#author: "AI"
#image: "No idea what I want here for now. Would be fun if this were an AI-generated image."
#slug: "Not sure what this is currently"
#description: "Generated description of the blog post"
#tags: ["AI", "News"]
#---

#TODO Another question is if we can't just ask ai to structure this in a specific way so we can parse it easily and afterwards create it like the structure above in the markdown file
#TODO We can also ask the AI to generate the markdown file directly BUT we need it to format like the whole blogpost with all the html tags
