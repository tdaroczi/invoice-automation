import os
import time
import traceback
from dotenv import load_dotenv
from src.email_service import EmailService
from src.drive_service import DriveService
from src.extraction_service import ExtractionService
from src.notion_service import NotionService
from src.notification_service import NotificationService

def main():
    load_dotenv()
    print("Invoice Automation System Started")
    
    notification_service = NotificationService()
    
    # Check interval in seconds (default 5 minutes)
    check_interval = int(os.getenv("CHECK_INTERVAL", 300))
    
    try:
        # Initialize services
        email_service = EmailService()
        drive_service = DriveService()
        extraction_service = ExtractionService()
        notion_service = NotionService()
        
        print("Services initialized successfully.")
        
        while True:
            try:
                print(f"Checking for new invoices... (Interval: {check_interval}s)")
                emails = email_service.fetch_invoices()
                
                if not emails:
                    print("No new invoices found.")
                else:
                    for msg, pdf_paths in emails:
                        print(f"Processing email: {msg.subject}")
                        
                        try:
                            for pdf_path in pdf_paths:
                                print(f"  Processing file: {pdf_path}")
                                
                                # 1. Upload to Drive
                                file_url = drive_service.upload_file(pdf_path)
                                if not file_url:
                                    raise Exception("Failed to upload to Drive")
                                
                                # 2. Extract Data
                                data = extraction_service.extract_data(pdf_path)
                                data['file_url'] = file_url
                                print(f"    Extracted: {data}")
                                
                                # 3. Add to Notion
                                notion_service.add_invoice(data)
                                
                            # 4. Mark as read
                            # email_service.mark_as_read(msg.uid)
                            print(f"Finished processing email: {msg.subject}")
                            
                        except Exception as e:
                            error_msg = f"Error processing email '{msg.subject}': {str(e)}\n{traceback.format_exc()}"
                            print(error_msg)
                            notification_service.send_error_alert(msg.subject, error_msg, context="Processing Email Loop")
            
            except Exception as e:
                # Catch errors in the main loop to prevent crash
                error_msg = f"Error in main loop: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                notification_service.send_error_alert("Main Loop Error", error_msg, context="Main Loop")
            
            # Wait for next check
            time.sleep(check_interval)

    except Exception as e:
        error_msg = f"Critical System Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        notification_service.send_error_alert("System Crash", error_msg, context="Main Initialization")

if __name__ == "__main__":
    main()
