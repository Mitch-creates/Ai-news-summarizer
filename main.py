import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from email_processing.gmail_interactions import fetch_emails
from database.db_operations import initialize_database, insert_blogpost, insert_email, get_all_emails, check_if_email_exists_by_gmail_id
from entities.Email import Email
from enums.newsletters import Newsletters
from blog.blogpost_creator import create_blogpost

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from file_processing.markdown_file_creator import generate_markdown_file  # Ensure file_processing is in the same directory or update the import path

load_dotenv("config/environment_variables.env")

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    

    # Step 2: Fetch newsletter emails
    active_newsletters = [newsletter.value for newsletter in Newsletters.__members__.values() if newsletter.active]
    print(f"Active newsletters: {active_newsletters}")

    all_bodies = []  # List of all email bodies
    emails = fetch_emails(service, active_newsletters)

    

    
    for email in emails:
            sender = email.sender_name  # Extract sender name
            subject = email.subject  # Extract email subject
            body = email.body  # Extract full email body
            date = email.date  # Extract email date
            sender_email = email.sender_email  # Extract sender email
            email_gmail_id = email.gmail_id # Extract unique email ID
    
            # Check if the email already exists in the database
            if not check_if_email_exists_by_gmail_id(email_gmail_id):
                email_object = Email(
                sender_name=sender,
                date=date,
                subject=subject,
                body=body,
                sender_email=sender_email,
                gmail_id=email_gmail_id,
                published=False
                )
                insert_email(email_object)
                print(f"Inserted email from {sender} with subject '{subject}' into the database.")
            else:
                print(f"Email from {sender} with subject '{subject}' already exists in the database.")
    
            # Fetch and print all emails from the database
    all_emails = get_all_emails()
    
    print(f"Response by Chatgpt=")
    newly_created_blogpost = create_blogpost(emails)
    generate_markdown_file(newly_created_blogpost)
    print(newly_created_blogpost)

if __name__ == "__main__":
    initialize_database()
    main()
    print("Done")
