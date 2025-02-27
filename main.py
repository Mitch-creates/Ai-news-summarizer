from googleapiclient.discovery import build
from gmail_auth import authenticate_gmail  # Import your authentication function
from fetch_emails import fetch_emails_and_summarize  # Import function to get emails
from summarizer import summarize_email

def main():
    # Step 1: Authenticate with Gmail
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

   
    # Step 2: Fetch newsletter emails
    newsletters = [
    #"dan@tldrnewsletter.com",
    #"team@bensbites.co",
    "therundownai@mail.beehiiv.com",
    #"michielvandevyver@gmail.com"
]
    emails = fetch_emails_and_summarize(service, newsletters)
    print(f"!!!!!!Number of emails fetched: {len(emails)}")

    # Step 3: Print emails to verify output
    for email in emails:
        sender = email['sender']  # Extract sender name
        original_body = email['body']  # Extract full email body
        summary = summarize_email(original_body)  # Pass to OpenAI

        # Print results
        print(f"Sender: {sender}\n")
        print("Original Email Body:\n")
        print(original_body[:1000])  # Print first 1000 chars for readability
        print("\n---\nSummary:\n")
        print(summary)
        print("\n" + "="*50 + "\n")
    
    print("Done!")

if __name__ == "__main__":
    main()
