import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

class SheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self):
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        if not self.service_account_file:
            # Try to read from content variable if file path not set (for cloud deployment)
            pass 
            
        if not self.spreadsheet_id:
            print("Warning: GOOGLE_SHEET_ID not set. Logging to Sheets disabled.")
            self.service = None
            return

        try:
            self.creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            print(f"Error initializing SheetsService: {e}")
            self.service = None

    def log(self, level: str, message: str, context: str = ""):
        """
        Appends a log entry to the configured Google Sheet.
        Columns: Timestamp, Level, Message, Context
        """
        if not self.service:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[timestamp, level, message, context]]
        
        body = {
            'values': values
        }
        
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="A:D", # Append to first 4 columns
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            # print(f"Logged to Sheets: {message}") # Optional: avoid cluttering console
        except Exception as e:
            print(f"Failed to log to Sheets: {e}")
