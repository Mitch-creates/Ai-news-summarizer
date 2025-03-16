import argparse
from datetime import datetime
import email
import sys
import time
from dotenv import load_dotenv
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth.gmail_auth import authenticate_gmail 
from database import db_operations
from email_processing.gmail_interactions import apply_label_to_multiple_emails, fetch_sunday_emails, fetch_wednesday_emails, rollback_email_status, rollback_multiple_emails_statuses
from database.db_operations import initialize_database, insert_email, check_if_email_exists_by_gmail_id
from entities.Email import Email
from enums.blogpost_subject import BlogPostSubject
from enums.gmail_labels import GmailLabels
from enums.newsletters import Newsletters
from blog.blogpost_creator import create_blogpost, generate_markdown_file
from git_processing.git_operations import commit_and_push_all, merge_pull_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.getLogger().handlers[0].flush = sys.stdout.flush
logging.getLogger().setLevel(logging.INFO)

# Supported subjects
SUBJECTS = ["AI", "TECH", "SCIENCE"]
blogposts_to_commit = []  # List to track blog posts that need committing

def get_active_newsletters(subject):
    """Fetch active newsletters for a given subject."""
    return [newsletter.email for newsletter in Newsletters if newsletter.active and newsletter.subject == subject]

def fetch_emails_for_today(service, active_newsletters, today):
    """Determine the day and fetch emails accordingly."""

    try:
        if today == "Sunday":
            logging.info("Running Sunday email fetch...")
            return fetch_sunday_emails(service, active_newsletters)
        elif today == "Wednesday":
            logging.info("Running Wednesday email fetch...")
            return fetch_wednesday_emails(service, active_newsletters)
        else:
            logging.warning("Script executed on an unintended day. Skipping email fetch.")
            return []
    except HttpError as e:
        logging.error(f"Gmail API error while fetching emails: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching emails: {e}")
        return []
    
def parse_email_date(date_string):
    """Parses an email date string into a Python datetime object."""
    try:
        parsed_date = email.utils.parsedate_to_datetime(date_string)
        return parsed_date
    except Exception as e:
        logging.error(f"Invalid date format: {date_string} - Error: {e}")
        return None  # Return None so we can handle it gracefully

def process_emails(emails):
    """Process and store emails in the database."""
    if not emails:
        logging.info("No new emails fetched. Skipping processing.")
        return
    
    for email in emails:
        try:
            if not check_if_email_exists_by_gmail_id(email.gmail_id):
                email_object = Email(
                    sender_name=email.sender_name,
                    date=parse_email_date(email.date),
                    subject=email.subject,
                    body=email.body,
                    sender_email=email.sender_email,
                    gmail_id=email.gmail_id,
                    published=False
                )
                insert_email(email_object)
                logging.info(f"Inserted email from {email.sender_name} with subject '{email.subject}' into the database.")
            else:
                logging.info(f"Email from {email.sender_name} with subject '{email.subject}' already exists in the database.")
        except Exception as e:
            logging.error(f"Error processing email {email.gmail_id}: {e}")

def generate_blogpost(emails, subject, today):
    """Generate a blog post from emails and publish it."""
    if not emails:
        logging.info(f"No emails found for {subject}. Skipping blog post generation.")
        return
    
    try:
        blogpost = create_blogpost(emails, subject, today)
        blogpost_dto = generate_markdown_file(blogpost)
        updated_blogpost = db_operations.update_blogpost(blogpost_dto.id, blogpost_dto)

        logging.info(f"Generated blog post for {subject}.")
        return updated_blogpost  # Add to list for later Git committing

    except Exception as e:
        logging.error(f"Error during blog post generation/publishing for {subject}: {e}")
        return None

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run the AI News Summary script.")
    parser.add_argument("--day", type=str, choices=["Sunday", "Wednesday"], help="Manually specify the day for testing.")
    args = parser.parse_args()
    emails_to_update_labels = []  # List to track emails for label updates

    # Use the argument if provided, otherwise use today's actual day
    today = args.day if args.day else datetime.today().strftime('%A')
    try:
        # Step 1: Authenticate with Gmail API
        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)

        # Step 2: Fetch active newsletters and generate blog posts for multiple subjects
        for subject in SUBJECTS:
            emails = []  # Reset emails for each subject
            logging.info(f"Processing {subject} newsletters...")
            subject = BlogPostSubject[subject]
            active_newsletters = get_active_newsletters(subject)

            if not active_newsletters:
                logging.info(f"No active newsletters added for {subject} or they're not active (bool isn't True). Skipping to next subject.")
                continue  

            emails = fetch_emails_for_today(service, active_newsletters, today)

            if not emails:
                logging.info(f"No emails found for {subject}. Skipping to next subject.")
                continue

            process_emails(emails)
            blogpost = generate_blogpost(emails, subject, today)
            if blogpost: 
                apply_label_to_multiple_emails(service, "me", emails, "Label_6126309069161477633") 
                emails_to_update_labels.extend(emails)  # Add emails to the list for label updates
                blogposts_to_commit.append(blogpost)
            else:
                logging.warning(f"Blog post generation failed for {subject}. Resetting email labels.")
                rollback_multiple_emails_statuses(service, "me", emails)

            logging.info(f"Completed processing blogpost for {subject} newsletters.")
            time.sleep(5)  # Sleep to avoid hitting API limits
        
        if blogposts_to_commit:
            logging.info("Committing and pushing all generated blog posts in a single push...")
            pr_number = commit_and_push_all(blogposts_to_commit)
            merge_pull_request(pr_number)
            apply_label_to_multiple_emails(service, "me", emails_to_update_labels, "Label_3076953365604997473")
            logging.info(f"Blog posts committed and pushed successfully. PR Number: {pr_number}")
        else:
            logging.info("No blog posts generated. Skipping GitHub commit.")

        logging.info("All blog post generation completed successfully.")

    except HttpError as e:
        logging.error(f"Gmail API error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    db_operations.initialize_database()
    main()
