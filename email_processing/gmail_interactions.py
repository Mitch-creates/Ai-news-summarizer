import os
import base64
from email.utils import parseaddr
import re
from googleapiclient.discovery import build
from blog.blogpost_creator import create_blogpost
from dotenv import load_dotenv
from entities.Email import Email  # Adjust the import path as necessary
from enums.gmail_labels import GmailLabels  # Adjust the import path as necessary

# Load environment variables
load_dotenv(dotenv_path="config/environment_variables.env")

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")

def fetch_sunday_emails(service, newsletters):
    """Fetches AI newsletter emails from the past week on Sunday."""
    query = ' OR '.join([f'from:{sender}' for sender in newsletters if isinstance(sender, str) and '@' in sender]) + ' newer_than:7d'  # Fetch last 7 days
    print(f"Constructed Query (Sunday Fetch): {query}")  # Debugging statement
    return fetch_emails(service, query)


def fetch_wednesday_emails(service, newsletters):
    """Fetches AI newsletter emails from Sunday to Wednesday (3-day window)."""
    query = ' OR '.join([f'from:{sender}' for sender in newsletters if isinstance(sender, str) and '@' in sender]) + ' newer_than:3d'  # Fetch last 3 days
    print(f"Constructed Query (Wednesday Fetch): {query}")  # Debugging statement
    return fetch_emails(service, query)


def fetch_emails(service, query):
    """Fetches newsletter emails based on a given Gmail query."""
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    
    print(f"Number of messages found: {len(messages)}")  # Debugging statement
    
    if not messages:
        print("No new newsletters found.")
        return []

    emails = []
    for message in messages:
        mark_email_as_read(service, "me", message["id"])
        emails.append(create_email_object(*get_email_content(service, "me", message["id"])))

    return emails

def create_email_object(subject, body, sender_name, sender_email, date, gmail_id):
    """Creates an Email object from the Gmail API result."""
    email_obj = Email(
        sender_name=sender_name, 
        date=date, 
        subject=subject, 
        body=body, 
        sender_email=sender_email, 
        gmail_id=gmail_id)
    return email_obj

def get_email_content(service, user_id, email_id):
    """Fetches and decodes the email content."""
    message = service.users().messages().get(userId=user_id, id=email_id, format="full").execute()
    payload = message["payload"]
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender = next((h['value'] for h in headers if h['name'] == "From"), "Unknown Sender")
    date = next((h["value"] for h in headers if h["name"] == "Date"), "No Date")

    sender_name, sender_email = parseaddr(sender)

    extracted_body = extract_email_body(payload)

    body_without_emojis = remove_emojis(extracted_body)

    cleaned_body = clean_newsletter_body(body_without_emojis)

    return subject, cleaned_body, sender_name, sender_email, date, email_id

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

def clean_newsletter_body(text):
    """Cleans up the newsletter content by removing unnecessary elements like links, ads, and tracking info."""
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove promotional text and subscription-related sections
    text = re.sub(r'\b(SIGN UP|ADVERTISE|VIEW ONLINE|GET STARTED HERE|APPLY HERE|TRACK YOUR REFERRALS|SHARE YOUR REFERRAL LINK|MANAGE YOUR SUBSCRIPTIONS|UNSUBSCRIBE)\b.*', '', text, flags=re.IGNORECASE)

    # Remove sponsor mentions (e.g., "TOGETHER WITH [Regal]")
    text = re.sub(r'\b(TOGETHER WITH|SPONSORED BY|SPONSOR)\b.*', '', text, flags=re.IGNORECASE)

    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '', text)

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n', text)

    # Remove citations like [10], [25], etc.
    text = re.sub(r'\[\d+\]', '', text)

    return text.strip()

def mark_email_as_read(service, user_id, email_id):
    """Marks an email as read by removing the UNREAD label."""
    service.users().messages().modify(
        userId=user_id,
        id=email_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()

def mark_email_as_unread(service, user_id, email_id):
    """Marks an email as unread by adding the UNREAD label."""
    service.users().messages().modify(
        userId=user_id,
        id=email_id,
        body={'addLabelIds': ['UNREAD']}
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

def apply_label_to_multiple_emails(service, user_id, emails, label_id):
    """Applies a label to multiple emails."""
    email_ids = [email.gmail_id for email in emails]
    for email_id in email_ids:
        apply_label_to_email(service, user_id, email_id, label_id)

def rollback_email_status(service, user_id, email):
    """Resets labels if a blog post is not created successfully."""
    email_id = email.gmail_id
    reset_labels(service, user_id, email_id, ["Label_3076953365604997473", "Label_6126309069161477633"])
    mark_email_as_unread(service, user_id, email_id)
    print(f"Email {email_id} rolled back to UNREAD status.")

def rollback_multiple_emails_statuses(service, user_id, emails):
    """Resets labels for multiple emails if blog posts are not created successfully."""
    for email in emails:
        reset_labels(service, user_id, email.gmail_id, ["Label_3076953365604997473", "Label_6126309069161477633"])
        mark_email_as_unread(service, user_id, email.gmail_id)
        print(f"Email {email.gmail_id} rolled back to READ status.")

# PUBLISHED -> Label_3076953365604997473
# PARSED -> Label_6126309069161477633

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
        reset_labels(service, user_id, message["id"], ["Label_3076953365604997473", "Label_6126309069161477633"])

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F700-\U0001F77F"  # Alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric shapes
        "\U0001F800-\U0001F8FF"  # Supplemental arrows
        "\U0001F900-\U0001F9FF"  # Supplemental symbols
        "\U0001FA00-\U0001FA6F"  # Chess symbols
        "\U0001FA70-\U0001FAFF"  # Other symbols
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)