import os
import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

class SheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self):
        self.service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        if not self.spreadsheet_id:
            print("Warning: GOOGLE_SHEET_ID not set. Logging to Sheets disabled.")
            self.service = None
            return

        try:
            creds = None
            # First, try to treat it as a file path
            if self.service_account_info and os.path.exists(self.service_account_info):
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_info, scopes=self.SCOPES
                )
            else:
                # If file doesn't exist, try to parse the variable content as JSON
                try:
                    if self.service_account_info:
                        info = json.loads(self.service_account_info)
                        creds = service_account.Credentials.from_service_account_info(
                            info, scopes=self.SCOPES
                        )
                except json.JSONDecodeError:
                     # Try fallback variable GOOGLE_SERVICE_ACCOUNT_JSON
                    json_content = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
                    if json_content:
                        info = json.loads(json_content)
                        creds = service_account.Credentials.from_service_account_info(
                            info, scopes=self.SCOPES
                        )

            if not creds:
                 print("Warning: Could not authenticate SheetsService (no valid creds found).")
                 self.service = None
                 return

            self.creds = creds
            self.service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            print(f"Error initializing SheetsService: {e}")
            self.service = None

    def log(self, level: str, message: str, context: str = ""):
        """
        Appends a log entry to the configured Google Sheet (Log sheet).
        Columns: Timestamp, Level, Message, Context
        """
        if not self.service:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[timestamp, level, message, context]]
        
        self._append_row("Log!A:D", values)

    def add_invoice(self, data: dict):
        """
        Appends invoice data to the 'Invoices' sheet.
        Expected columns:
        1. Dokumentum típusa
        2. Díjbekérő / Számla száma
        3. Kiállító neve
        4. Kiállító adószáma
        5. Díjbekérő kelte
        6. Fizetési határidő
        7. Bruttó összeg
        8. Megjegyzés / Közlemény
        9. Vevő neve
        """
        if not self.service:
            return

        values = [[
            data.get('type', ''),
            data.get('invoice_number', ''),
            data.get('vendor', ''),
            data.get('vendor_tax_id', ''),
            data.get('issue_date', ''),
            data.get('due_date', ''),
            data.get('amount', ''),
            data.get('comment', ''), # Not extracted yet, but placeholder
            data.get('buyer', '')
        ]]
        
        # Append to the first sheet (or specific sheet if named)
        # Assuming the main sheet is the first one or named 'Munkalap1' or similar.
        # We'll use "A:I" which usually appends to the first sheet's first empty row.
        self._append_row("A:I", values)

    def _append_row(self, range_name: str, values: list):
        try:
            body = {'values': values}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
        except Exception as e:
            print(f"Failed to append to Sheets ({range_name}): {e}")
