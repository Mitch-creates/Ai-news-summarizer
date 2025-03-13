import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from database import db_operations
from email_processing.gmail_interactions import fetch_emails
from database.db_operations import initialize_database, insert_email, get_all_emails, check_if_email_exists_by_gmail_id
from entities.Email import Email
from enums.newsletters import Newsletters
from blog.blogpost_creator import create_blogpost, generate_markdown_file
from git_processing.git_operations import commit_and_push_to_github, merge_pull_request

load_dotenv("config/environment_variables.env")

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    

    # Step 2: Fetch newsletter emails
    active_newsletters = [newsletter.value for newsletter in Newsletters.__members__.values() if newsletter.active]

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
    
   
    newly_created_blogpost = create_blogpost(emails)
    # blogpostdto = generate_markdown_file(newly_created_blogpost)
    # updated_blogpost = db_operations.update_blogpost(blogpostdto.id, blogpostdto)

    # # # print(blogpostdto)

    # pr_number = commit_and_push_to_github(updated_blogpost)
    # merge_pull_request(pr_number)


if __name__ == "__main__":
    initialize_database()
    main()
    print("Done")
