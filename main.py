from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from email_processing.gmail_interactions import fetch_emails
from database.db_operations import create_connection, create_table, insert_email
from enums.newsletters import Newsletters

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    # Step 2: Fetch newsletter emails
    newsletters = [newsletter.email for newsletter in Newsletters if newsletter.active]

    all_bodies = []  # List of all email bodies
    emails = fetch_emails(service, newsletters)
    print(f"!!!!!!Number of emails fetched: {len(emails)}")

    # Step 3: Store emails in the database
    database = "emails.db"
    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
        for email in emails:
            sender = email.sender_name  # Extract sender name
            subject = email.subject  # Extract email subject
            body = email.body  # Extract full email body
            date = email.date  # Extract email date
            sender_email = email.sender_email  # Extract sender email
            unique_id = email.unique_id  # Extract unique email ID

            email_data = (sender, date, subject, body, sender_email, unique_id, False)
            insert_email(conn, email_data)

            # Print results
            print(f"Sender: {sender}\n")
            print("Original Email Body:\n")
            print(email.body)
            print("\n" + "="*50 + "\n")
        
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == "__main__":
    main()
