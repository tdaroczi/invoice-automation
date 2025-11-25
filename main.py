import os
import time
import datetime
import traceback
from dotenv import load_dotenv
from src.email_service import EmailService
from src.drive_service import DriveService
from src.email_service import EmailService
from src.drive_service import DriveService
from src.extraction_service import ExtractionService
# from src.notion_service import NotionService # Deprecated
from src.notification_service import NotificationService
from src.sheets_service import SheetsService

def main():
    load_dotenv()
    print("Invoice Automation System Started")
    
    notification_service = NotificationService()
    
    # Check interval: 1 hour (3600 seconds)
    check_interval = 3600
    
    try:
        # Initialize services
        email_service = EmailService()
        drive_service = DriveService()
        extraction_service = ExtractionService()
        # notion_service = NotionService() # Deprecated
        sheets_service = SheetsService()
        
        print("Services initialized successfully.")
        sheets_service.log("INFO", "System initialized and started.")
        
        while True:
            try:
                now = datetime.datetime.now()
                current_hour = now.hour
                
                # Run only between 7:00 and 19:00 (inclusive)
                if 7 <= current_hour <= 19:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Checking for new invoices...")
                    
                    try:
                        emails = email_service.fetch_invoices()
                        
                        if not emails:
                            print("No new invoices found.")
                            # sheets_service.log("INFO", "Check completed. No new invoices.", context="Main Loop")
                        else:
                            for msg, pdf_paths in emails:
                                print(f"Processing email: {msg.subject}")
                                sheets_service.log("INFO", f"Processing email: {msg.subject}", context="Email Processing")
                                
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
                                        
                                        # 3. Add to Sheets (formerly Notion)
                                        sheets_service.add_invoice(data)
                                        
                                        sheets_service.log("INFO", f"Successfully processed invoice: {data.get('vendor')} - {data.get('amount')}", context="Invoice Success")
                                        
                                    # 4. Mark as read
                                    email_service.mark_as_read(msg.uid)
                                    print(f"Finished processing email: {msg.subject}")
                                    
                                except Exception as e:
                                    error_msg = f"Error processing email '{msg.subject}': {str(e)}"
                                    print(error_msg)
                                    sheets_service.log("ERROR", error_msg, context="Processing Loop")
                                    notification_service.send_error_alert(msg.subject, error_msg, context="Processing Email Loop")
                    except Exception as e:
                         # Catch errors during fetch
                        error_msg = f"Error fetching emails: {str(e)}"
                        print(error_msg)
                        sheets_service.log("ERROR", error_msg, context="Fetch Loop")
                        
                else:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Outside working hours (7-19). Sleeping...")

            except Exception as e:
                # Catch errors in the main loop to prevent crash
                error_msg = f"Error in main loop: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                sheets_service.log("CRITICAL", "Main loop crashed (restarting)", context="Main Loop")
                notification_service.send_error_alert("Main Loop Error", error_msg, context="Main Loop")
            
            # Wait for next check
            time.sleep(check_interval)

    except Exception as e:
        error_msg = f"Critical System Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # Try to log if sheets service was initialized, otherwise just print
        try:
            if 'sheets_service' in locals():
                sheets_service.log("CRITICAL", "System crashed completely", context="Startup")
        except:
            pass
        notification_service.send_error_alert("System Crash", error_msg, context="Main Initialization")

if __name__ == "__main__":
    main()
