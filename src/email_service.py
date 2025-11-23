import os
import requests
from imap_tools import MailBox, AND
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
import re

class EmailService:
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST")
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")
        
        if not all([self.host, self.user, self.password]):
            raise ValueError("Email credentials not found in environment variables.")

    def fetch_invoices(self, folder="INBOX") -> List[Tuple[object, List[str]]]:
        """
        Fetches unread emails containing 'invoice' or 'számla' in subject or body.
        Returns a list of tuples: (email_object, list_of_pdf_paths)
        """
        processed_emails = []
        
        try:
            with MailBox(self.host).login(self.user, self.password) as mailbox:
                mailbox.folder.set(folder)
                
                # Search for unread emails with keywords
                criteria = AND(seen=False, subject=["invoice", "számla", "díjbekérő"])
                
                for msg in mailbox.fetch(criteria, mark_seen=False):
                    print(f"Processing email: {msg.subject}")
                    pdf_files = self._download_attachments(msg)
                    
                    if not pdf_files:
                        print(f"No PDF attachments found in: {msg.subject}. Checking for links...")
                        pdf_files = self._download_from_links(msg)
                    
                    if pdf_files:
                        processed_emails.append((msg, pdf_files))
                    else:
                        print(f"No PDF found (attachment or link) in: {msg.subject}")
                        
        except Exception as e:
            print(f"Error fetching emails: {e}")
            raise e # Re-raise to be caught by main loop
            
        return processed_emails

    def _download_attachments(self, msg) -> List[str]:
        """
        Downloads PDF attachments from the email message.
        Returns a list of local file paths.
        """
        saved_files = []
        download_folder = "downloads"
        os.makedirs(download_folder, exist_ok=True)

        for att in msg.attachments:
            if att.filename.lower().endswith(".pdf"):
                filepath = os.path.join(download_folder, att.filename)
                with open(filepath, "wb") as f:
                    f.write(att.payload)
                saved_files.append(filepath)
                print(f"Downloaded attachment: {filepath}")
                
        return saved_files

    def _download_from_links(self, msg) -> List[str]:
        """
        Parses email body for download links and downloads the PDF.
        Returns a list of local file paths.
        """
        saved_files = []
        download_folder = "downloads"
        os.makedirs(download_folder, exist_ok=True)
        
        html_body = msg.html
        if not html_body:
            return []

        soup = BeautifulSoup(html_body, 'html.parser')
        links = soup.find_all('a', href=True)
        
        # Keywords to look for in link text or class/id
        keywords = ["számla letöltése", "számla megtekintése", "download invoice", "számla"]
        
        for link in links:
            text = link.get_text().lower().strip()
            href = link['href']
            
            # Check if link text matches keywords
            if any(kw in text for kw in keywords):
                print(f"Found potential invoice link: {href}")
                try:
                    filepath = self._download_file_from_url(href, download_folder)
                    if filepath:
                        saved_files.append(filepath)
                        # Assume one invoice per email usually, but let's keep looking just in case? 
                        # Usually one main CTA is enough.
                        break 
                except Exception as e:
                    print(f"Failed to download from link {href}: {e}")

        return saved_files

    def _download_file_from_url(self, url: str, folder: str) -> Optional[str]:
        try:
            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()
            
            # Try to get filename from headers
            content_disposition = response.headers.get('content-disposition')
            filename = None
            if content_disposition:
                fname = re.findall("filename=(.+)", content_disposition)
                if fname:
                    filename = fname[0].strip('"')
            
            if not filename:
                # Fallback: generate a name based on timestamp
                import time
                filename = f"invoice_download_{int(time.time())}.pdf"
                
            if not filename.lower().endswith('.pdf'):
                # Sometimes the link is a viewer, not direct PDF. 
                # If content-type is not pdf, we might be in trouble.
                if 'application/pdf' not in response.headers.get('Content-Type', ''):
                    print(f"URL did not return a PDF: {url}")
                    return None
                filename += ".pdf"

            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded from URL: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading from URL {url}: {e}")
            return None

    def mark_as_read(self, msg_uid, folder="INBOX"):
        """Marks an email as read."""
        try:
            with MailBox(self.host).login(self.user, self.password) as mailbox:
                mailbox.folder.set(folder)
                mailbox.flag([msg_uid], '\\Seen', True)
        except Exception as e:
            print(f"Error marking email as read: {e}")
