import os
import pickle
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # Update with required scopes

def authenticate_gmail():
    print("Starting Gmail authentication...")
    creds = None

    if os.path.exists("token.pickle"):
        print("Found existing token.pickle file. Loading credentials...")
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
                print("Token refreshed successfully!")
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
                print("Could not refresh token, re-authenticating...")
                creds = None  # Force new authentication
        if not creds:
            print("No valid credentials found. Opening browser for authentication...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)
            except Exception as e:
                logging.error(f"Error during authentication: {e}")
                return None

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
            print("Saved new credentials to token.pickle")

    print("Authentication successful!")
    return creds

if __name__ == "__main__":
    authenticate_gmail()
