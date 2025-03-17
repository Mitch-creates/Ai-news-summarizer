import json
import logging
import sys
from jinja2 import Template
import openai
import os
from dotenv import load_dotenv
import yaml
from bs4 import BeautifulSoup
from datetime import datetime

from entities.Blogpost import BlogPost
from entities.BlogpostDTO import BlogPostDTO
from entities.Blogpost_metadata import BlogPostMetadata
from enums.blogpost_status import BlogPostStatus
import database.db_operations
from enums.blogpost_subject import BlogPostSubject

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

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

def load_prompts():
    with open("yaml_data/prompts.yaml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def get_prompt(subject: BlogPostSubject, today) -> str:
    """Loads the prompt based on the subject."""
    prompts = load_prompts()
    weekday = today

    if subject.name not in prompts:
        raise ValueError(f"No prompt found for {subject.name}")

    prompt_template = prompts[subject.name]

    print(f"Prompt template for {subject.name}: {prompt_template}")  # Debugging statement

    if isinstance(prompt_template, str):
        template = Template(prompt_template)
        return template.render(day=weekday)
    else:
        raise ValueError(f"Invalid prompt format for {subject.name}")

def insert_emaillist_in_prompt(emails: list, prompt: str) -> str:
    """Inserts the emails into the prompt."""
    body = format_email_body_for_openai(emails)
    final_prompt = prompt.format(body=body)
    if not final_prompt:
        raise ValueError("Prompt is empty after inserting emaillist. Please check the prompt file.")
    return final_prompt
    
def create_blogpost(emails: list, blogpost_subject: BlogPostSubject, today) -> BlogPostDTO:
    """Summarizes the email body using OpenAI's GPT-3.5 model."""
    prompt = get_prompt(blogpost_subject, today)
    # Check if the emails list is empty
    if not emails:
        raise ValueError("No emails available for processing.")
    
    
    final_prompt = insert_emaillist_in_prompt(emails, prompt)
    # print short version of final_prompt for debugging
    # Check if the prompt is empty or None

    print(f"Preparing request for {blogpost_subject.value.capitalize()} blog post...")
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            model=model,
            max_tokens=1000
        )
        response_with_backticks = response.choices[0].message.content

        if not isinstance(response_with_backticks, str):
            raise ValueError("Response is not a valid string.")
        
        response_with_backticks = response_with_backticks.strip()
        cleaned_response = response_with_backticks.strip('```yaml').strip('```')

        blogpost = create_blogpost_instance_from_yaml(cleaned_response, prompt, len(emails), response.usage.total_tokens, list(set(email.sender_name for email in emails)), blogpost_subject, today)
        
        
        newly_created_blogpost = database.db_operations.insert_blogpost(blogpost, generate_next_slug(today, blogpost))
        
        return newly_created_blogpost
    except GeneratorExit:
        print("Generator was forcefully closed.")
    except Exception as e:
        print(f"Error in generating blogpost: {e}")
        return "Failed to generate blogpost"
    
# Ensure the "json_data" directory exists
DATA_DIR = os.path.join(os.getcwd(), "json_data")  # Gets the full path
os.makedirs(DATA_DIR, exist_ok=True)  # Creates the directory if it doesn't exist

# Path to the JSON file
COUNTER_FILE = os.path.join(DATA_DIR, "slug_counters.json")

def load_counters():
    """Loads the counters from a JSON file or initializes an empty dictionary."""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return json.load(f)  # Try to load the JSON content
        except json.JSONDecodeError:  # Handle corrupted JSON
            print("Warning: JSON file was corrupted. Resetting it.")
            return {}  # Return an empty dict to reset it
    return {}  # If file doesn't exist, return an empty dict


def save_counters(counters):
    """Saves the counters to a JSON file safely."""
    temp_file = COUNTER_FILE + ".tmp"  # Use a temp file to prevent corruption
    with open(temp_file, "w") as f:
        json.dump(counters, f, indent=4)
    
    os.replace(temp_file, COUNTER_FILE)  # Replace the old file atomically


def generate_next_slug(today, blogpost : BlogPost) -> str:
    """Generates a unique slug based on a JSON-stored counter, starting at 1 if the subject is new."""
    assert today in ["Sunday", "Wednesday"], f"Invalid day: {today}"
    counters = load_counters()

    counter_key = f"{blogpost.blogpost_subject.name}-{today}"
    # If the subject is new, initialize it at 1
    counters[counter_key] = counters.get(counter_key, 0) + 1

    # Save updated counters
    save_counters(counters)

    slug_type = "weekly" if today == "Sunday" else "midweek"

    return f"{slug_type}-{blogpost.blogpost_subject.value.lower()}-news-{counters[counter_key]}"

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
    """Parses an OpenAI YAML response and ensures it's valid."""
    try:
        logging.info("Parsing YAML response...")

        # Ensure the response is not empty
        if not response or not response.strip():
            logging.error("Received an empty YAML response!")
            return None

        # Fix triple backtick markdown issue
        if "```" in response:
            logging.warning("Detected triple backticks in YAML. Removing them...")
            response = response.replace("```", "")

        parsed_data = yaml.safe_load(response)

        if not isinstance(parsed_data, dict):
            logging.error(f"Parsed YAML is not a dictionary: {parsed_data}")
            return None

        logging.info("Successfully parsed YAML.")
        return parsed_data

    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML response: {e}")
        return None

def create_blogpost_instance_from_yaml(response: str, prompt: str, amount_of_emails: int, amount_of_tokens: int, newsletter_sources: list, blogpost_subject: BlogPostSubject, today) -> BlogPost:
    """Creates a BlogPost instance from the parsed YAML response."""
    print("Michiel")

    print("🔍 Debugging `create_blogpost_instance_from_yaml()` Inputs:")
    print(f"Response: {response[:500]}")  # Log first 500 characters to prevent excessive output
    print(f"Prompt Used: {prompt[:500]}")
    print(f"Amount of Emails: {amount_of_emails}")
    print(f"Amount of Tokens: {amount_of_tokens}")
    print(f"Newsletter Sources: {newsletter_sources}")
    print(f"Blogpost Subject: {blogpost_subject}")
    parsed_data = parse_yaml_response(response)

    # Validate required fields
    required_fields = ["description", "content"]
    for field in required_fields:
        if field not in parsed_data:
            raise ValueError(f"Missing required field in response: {field}")
    
    
    
    print("🔍 Parsed YAML Response:")
    print(json.dumps(parsed_data, indent=2))  # Pretty-print parsed YAML
    
    metadata = BlogPostMetadata(
        title=create_title(blogpost_subject, today),
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
        published_weekday=datetime.now().strftime('%A'),
        markdown_file_path=None,
        status=BlogPostStatus.DRAFT,
        tags=json.dumps(parsed_data.get("tags", [])),  
        prompt_used=prompt,
        blogpost_subject=blogpost_subject, 
        blogpost_metadata=metadata
    )

    print("✅ Successfully Created BlogPost Instance:")
    print(f"BlogPost Title: {metadata.title}")
    print(f"BlogPost Description: {metadata.description}")
    print(f"Word Count: {blogpost.word_count}")
    print(f"Tags: {blogpost.tags}")

    return blogpost

def create_title(blogpost_subject: BlogPostSubject, today) -> str:
    """Creates a title for the blog post based on the subject and day of week."""
    day_of_week = today
    if (day_of_week == "Sunday"):
        return f"{blogpost_subject.value.capitalize()} Weekly Recap - {day_of_week} edition"
    elif (day_of_week == "Wednesday"):
        return f"{blogpost_subject.value.capitalize()} Midweek Update - {day_of_week} edition"


def remove_html_elements(html_content: str) -> str:
    """Removes HTML elements from the content to count the amount of words used for the blogpost."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

def generate_markdown_file(blogpostDTO: BlogPostDTO) -> BlogPostDTO:
    """Generate a markdown file from a Blogpost object"""
    try:
        # Get the current directory of the script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        if "GITHUB_ACTIONS" in os.environ:
            logging.info("Running in GitHub Actions environment.")
            blog_repo_path = os.path.join(os.getenv("GITHUB_WORKSPACE", os.getcwd()), "blog_repo")
        else:
            logging.info("Running in local environment.")
            blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH", "C:\\Users\\michi\\Projects\\News-summary-blog")

        # Construct the relative path to the target directory
        target_dir = os.path.join(blog_repo_path, "content/posts")
        target_dir = os.path.abspath(target_dir)  # Ensure absolute path

        # Define filename
        slug = blogpostDTO.blogpost_metadata.slug
        filename = f"{slug}.md"
        filepath = os.path.join(target_dir, filename)
        logging.info(f"Markdown file will be saved at: {filepath}")

        # Create front matter (YAML metadata)
        front_matter = {
            "layout": "post",
            "categories": [blogpostDTO.blogpost_subject],
            "tags": blogpostDTO.tags,
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
        logging.info(f"Markdown file created successfully at {filepath}")

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
