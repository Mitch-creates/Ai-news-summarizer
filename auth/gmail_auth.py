import os
import pickle
import google.auth
import webbrowser
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Enable debugging logs
logging.basicConfig(level=logging.DEBUG)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    print("Starting Gmail authentication...")  # Debugging statement
    creds = None

    # Register Chrome as default browser
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

    if os.path.exists("token.pickle"):
        print("Found existing token.pickle file. Loading credentials...")
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Opening browser for authentication...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)  # Opens browser for login
            except Exception as e:
                logging.error(f"Error during authentication: {e}")
                return

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
            print("Saved new credentials to token.pickle")

    print("Authentication successful!")
    return creds

if __name__ == "__main__":
    authenticate_gmail()
