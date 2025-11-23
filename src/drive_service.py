import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveService:
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self):
        self.service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        if not self.service_account_info:
             raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE environment variable not set.")
        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID environment variable not set.")

        try:
            # First, try to treat it as a file path
            if os.path.exists(self.service_account_info):
                self.creds = service_account.Credentials.from_service_account_file(
                    self.service_account_info, scopes=self.SCOPES
                )
            else:
                # If file doesn't exist, try to parse the variable content as JSON
                try:
                    info = json.loads(self.service_account_info)
                    self.creds = service_account.Credentials.from_service_account_info(
                        info, scopes=self.SCOPES
                    )
                except json.JSONDecodeError:
                    # Try fallback variable GOOGLE_SERVICE_ACCOUNT_JSON
                    json_content = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
                    if json_content:
                        info = json.loads(json_content)
                        self.creds = service_account.Credentials.from_service_account_info(
                            info, scopes=self.SCOPES
                        )
                    else:
                        raise ValueError(f"File not found and content is not valid JSON: {self.service_account_info}")

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
