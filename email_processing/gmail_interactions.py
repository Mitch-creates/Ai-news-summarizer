import os
import base64
import email
from email.utils import parseaddr
from googleapiclient.discovery import build
from blog.blogpost_creator import create_blogpost
from dotenv import load_dotenv
from entities.Email import Email  # Adjust the import path as necessary
from enums.gmail_labels import GmailLabels  # Adjust the import path as necessary

# Load environment variables
load_dotenv(dotenv_path="config/environment_variables.env")

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")

def fetch_emails(service, newsletters):
    """Fetches AI newsletter emails from the last 7 days and summarizes them."""
    query = ' OR '.join([f'from:{sender}' for sender in newsletters]) + ' newer_than:7d'  # Fetch last 7 days
    print(f"Constructed Query: {query}")  # Debugging statement
    results = service.users().messages().list(userId="me", q=query).execute()
    # Fetch the list of messages
    messages = results.get("messages", [])
    print(f"Number of messages found: {len(messages)}")  # Debugging statement

    if not messages:
        print("No new AI newsletters found.")
        return []
    
    emails = []
    for message in messages:
        emails.append(create_email_object(*get_email_content(service, "me", message["id"])))

    return emails

def create_email_object(subject, body, sender_name, sender_email, date, unique_id):
    """Creates an Email object from the Gmail API result."""
    email_obj = Email(sender_name, date, subject, body, sender_email, unique_id)
    return email_obj

def store_each_email_in_db(email_content):
    """Stores each email in the database."""

def check_for_duplicate_email_ids(email_ids):
    """Checks for duplicate email IDs in the database."""

def get_email_content(service, user_id, email_id):
    """Fetches and decodes the email content."""
    message = service.users().messages().get(userId=user_id, id=email_id, format="full").execute()
    payload = message["payload"]
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender = next((h['value'] for h in headers if h['name'] == "From"), "Unknown Sender")
    date = next((h["value"] for h in headers if h["name"] == "Date"), "No Date")

    sender_name, sender_email = parseaddr(sender)

    body = extract_email_body(payload)
    print(f"Extracted - Subject: {subject}, Sender: {sender_name} <{sender_email}>, Date: {date}, Body: {body[:100]}")

    return subject, body, sender_name, sender_email, date, email_id

def extract_email_body(payload):
    """Extracts email body, prioritizing text/plain but falling back to text/html."""
    if "parts" in payload and payload["parts"]:
        for part in payload["parts"]:
            if "parts" in part:  # Handle nested parts
                body = extract_email_body(part)
                if body:
                    return body
            if part["mimeType"] == "text/plain":
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            elif part["mimeType"] == "text/html":
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
    elif "body" in payload and "data" in payload["body"]:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    return "No content found."

def mark_email_as_read(service, user_id, email_id):
    """Marks an email as read by removing the UNREAD label."""
    service.users().messages().modify(
        userId=user_id,
        id=email_id,
        body={'removeLabelIds': [GmailLabels.UNREAD.value]}
    ).execute()

def create_label(service, user_id, label_name):
    """Creates a new label in the user's mailbox."""
    label = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created_label = service.users().labels().create(userId=user_id, body=label).execute()
    return created_label['id']

def apply_label_to_email(service, user_id, email_id, label_id):
    """Applies a label to an email."""
    service.users().messages().modify(
        userId=user_id,
        id=email_id,
        body={'addLabelIds': [label_id]}
    ).execute()

def reset_labels(service, user_id, email_id, label_ids):
    """Removes all labels from an email."""
    service.users().messages().modify(
        userId=user_id,
        id=email_id,
        body={'removeLabelIds': label_ids}
    ).execute()

def reset_process(service, user_id):
    """Resets the process by removing all custom labels from all emails."""
    results = service.users().messages().list(userId=user_id, q="label:PARSED OR label:PUBLISHED").execute()
    messages = results.get("messages", [])
    for message in messages:
        reset_labels(service, user_id, message["id"], [GmailLabels.PARSED.value, GmailLabels.PUBLISHED.value])