import os
import base64
import email
from googleapiclient.discovery import build
from summarizer import summarize_email
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="environment_variables.env")

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")

def fetch_emails_and_summarize(service, newsletters):
    """Fetches AI newsletter emails from the last 7 days and summarizes them."""
    query = f'({" OR ".join(f"from:{sender}" for sender in newsletters)}) newer_than:7d'  # Fetch last 7 days
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No new AI newsletters found.")
        return []

    summarized_emails = []
    for msg in messages:
        subject, body, sender = get_email_content(service, "me", msg["id"])
        summary = summarize_email(body)
        summarized_emails.append({"subject": subject, "body": body, "summary": summary, "sender": sender})

    return summarized_emails

def get_email_content(service, user_id, email_id):
    """Fetches and decodes the email content."""
    message = service.users().messages().get(userId=user_id, id=email_id, format="full").execute()
    payload = message["payload"]

    # Extract email subject
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender = sender = next((h['value'] for h in headers if h['name'] == "From"), "Unknown Sender")

    # Extract email body
    body = "No content found."
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break  # Stop at first text/plain part
            elif part["mimeType"] == "text/html":
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break  # Stop at first text/html part

    return subject, body, sender
