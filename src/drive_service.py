import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveService:
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self):
        self.service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID environment variable not set.")

        try:
            self.creds = None
            
            # 1. Try GOOGLE_SERVICE_ACCOUNT_JSON (Priority)
            if self.service_account_json:
                try:
                    info = json.loads(self.service_account_json)
                    self.creds = service_account.Credentials.from_service_account_info(
                        info, scopes=self.SCOPES
                    )
                    print("DEBUG: Authenticated using GOOGLE_SERVICE_ACCOUNT_JSON")
                except json.JSONDecodeError as e:
                    print(f"Warning: GOOGLE_SERVICE_ACCOUNT_JSON is invalid JSON: {e}")

            # 2. Try GOOGLE_SERVICE_ACCOUNT_FILE (Fallback)
            if not self.creds and self.service_account_info:
                # First, try to treat it as a file path
                if os.path.exists(self.service_account_info):
                    self.creds = service_account.Credentials.from_service_account_file(
                        self.service_account_info, scopes=self.SCOPES
                    )
                    print("DEBUG: Authenticated using GOOGLE_SERVICE_ACCOUNT_FILE (path)")
                else:
                    # If file doesn't exist, try to parse the variable content as JSON
                    try:
                        # Clean the string: remove whitespace and potential surrounding quotes
                        clean_info = self.service_account_info.strip().strip("'").strip('"')
                        
                        # Debug: Print info about the string (safe version)
                        print(f"DEBUG: Service Account Info Length: {len(clean_info)}")
                        if len(clean_info) < 20:
                             print(f"DEBUG: Starts with: {clean_info}...")
                        
                        info = json.loads(clean_info)
                        self.creds = service_account.Credentials.from_service_account_info(
                            info, scopes=self.SCOPES
                        )
                        print("DEBUG: Authenticated using GOOGLE_SERVICE_ACCOUNT_FILE (content)")
                    except json.JSONDecodeError as e:
                         print(f"JSON Decode Error in FILE variable: {e}")

            if not self.creds:
                 raise ValueError("Could not authenticate. Neither GOOGLE_SERVICE_ACCOUNT_JSON nor GOOGLE_SERVICE_ACCOUNT_FILE provided valid credentials.")

            self.service = build('drive', 'v3', credentials=self.creds)
        except Exception as e:
            raise ValueError(f"Failed to authenticate with Google Drive: {e}")

    def upload_file(self, file_path: str) -> str:
        """
        Uploads a file to the configured Google Drive folder.
        Returns the webViewLink of the uploaded file.
        """
        file_name = os.path.basename(file_path)
        
        file_metadata = {
            'name': file_name,
            'parents': [self.folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            print(f"File uploaded: {file.get('name')} (ID: {file.get('id')})")
            return file.get('webViewLink')
            
        except Exception as e:
            print(f"Error uploading file to Drive: {e}")
            return None
