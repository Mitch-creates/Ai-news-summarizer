from googleapiclient.discovery import build
from auth.gmail_auth import authenticate_gmail  # Import your authentication function
from email_processing.gmail_interactions import fetch_emails
from database.db_operations import create_connection, create_table, insert_email, get_all_emails, check_if_email_exists
from enums.newsletters import Newsletters
from blog.blogpost_creator import create_blogpost

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

            # Check if the email already exists in the database
            if not check_if_email_exists(conn, unique_id):
                email_data = (sender, date, subject, body, sender_email, unique_id, False)
                insert_email(conn, email_data)
                print(f"Inserted email from {sender} with subject '{subject}' into the database.")
            else:
                print(f"Email from {sender} with subject '{subject}' already exists in the database.")

        # Fetch and print all emails from the database
        all_emails = get_all_emails(conn)
        for row in all_emails:
            print(f"ID: {row[0]}, Sender: {row[1]}, Date: {row[2]}, Subject: {row[3]}, Body: {row[4][:100]}, Sender Email: {row[5]}, Unique ID: {row[6]}, Published: {row[7]}")

    
        
        conn.close()
    else:
        print("Error! Cannot create the database connection.")


    print(f"Response by Chatgpt=")
    print(create_blogpost(emails))

if __name__ == "__main__":
    main()
