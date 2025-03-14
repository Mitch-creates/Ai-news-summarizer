import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from database import db_operations
from email_processing.gmail_interactions import fetch_emails, fetch_sunday_emails
from database.db_operations import initialize_database, insert_email, get_all_emails, check_if_email_exists_by_gmail_id
from entities.Email import Email
from enums.blogpost_subject import BlogPostSubject
from enums.newsletters import Newsletters
from blog.blogpost_creator import create_blogpost, generate_markdown_file, get_prompt
from git_processing.git_operations import commit_and_push_to_github, merge_pull_request

load_dotenv("config/environment_variables.env")

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)
    
    # get Ai BlogPostSubject
    blogpost_subject = BlogPostSubject['AI']
    # Step 2: Fetch newsletter emails where subject is AI
    active_AI_newsletters = [newsletter.email for newsletter in Newsletters if newsletter.active == True and newsletter.subject == blogpost_subject]

    emails = fetch_sunday_emails(service, active_AI_newsletters)

    

    
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
    
    

    newly_created_blogpost = create_blogpost(emails, blogpost_subject)
    blogpostdto = generate_markdown_file(newly_created_blogpost)
    updated_blogpost = db_operations.update_blogpost(blogpostdto.id, blogpostdto)

    pr_number = commit_and_push_to_github(updated_blogpost)
    merge_pull_request(pr_number)


if __name__ == "__main__":
    initialize_database()
    main()
    print("Done")
