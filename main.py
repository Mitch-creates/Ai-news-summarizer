from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from email_processing.gmail_interactions import fetch_emails, create_label, apply_label_to_email, reset_process
from database.db_operations import create_connection, create_table, insert_email
from enums.gmail_labels import GmailLabels
from enums.newsletters import Newsletters

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    # Step 2: Create necessary labels
    user_id = "me"
    parsed_label_id = create_label(service, user_id, GmailLabels.PARSED.value)
    published_label_id = create_label(service, user_id, GmailLabels.PUBLISHED.value)

    #Step 3: Fetch newsletter emails
    newsletters = [newsletter.email for newsletter in Newsletters if newsletter.active]
    
    all_bodies = []  # List of all email bodies
    emails = fetch_emails(service, newsletters)
    print(f"!!!!!!Number of emails fetched: {len(emails)}")

    # Step 4: Store emails in the database and apply labels
    database = "emails.db"
    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
        for email in emails:
            sender = email['sender']  # Extract sender name
            subject = email['subject']  # Extract email subject
            body = email['body']  # Extract full email body
            summary = email['summary']  # Extract email summary
            email_id = email['unique_id']

            email_data = (sender, subject, body, summary)
            insert_email(conn, email_data)

            # Apply PARSED label to the email
            #apply_label_to_email(service, user_id, email_id, parsed_label_id)

            # Print results
            print(f"Sender: {sender}\n")
            print("Original Email Body:\n")
            print(body[:1000])  # Print first 1000 chars for readability
            print("\n---\nSummary:\n")
            print(summary)
            print("\n" + "="*50 + "\n")
        
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == "__main__":
    main()
