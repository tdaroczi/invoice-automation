import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveService:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self):
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        if not self.service_account_file or not self.folder_id:
            raise ValueError("Google Drive configuration missing.")
            
        self.creds = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=self.SCOPES
        )
        self.service = build('drive', 'v3', credentials=self.creds)

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
