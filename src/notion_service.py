import os
from notion_client import Client
from typing import Dict, Any

class NotionService:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not self.token or not self.database_id:
            raise ValueError("Notion credentials not found.")
            
        self.client = Client(auth=self.token)

    def add_invoice(self, data: Dict[str, Any]):
        """
        Adds a new invoice entry to the Notion database.
        Data dict should contain: 'vendor', 'date', 'amount', 'file_url'
        """
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"{data.get('vendor', 'Unknown')} - {data.get('date', 'No Date')}"
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": data.get('date')
                }
            } if data.get('date') else None,
            "Amount": {
                "number": data.get('amount')
            },
            "File": {
                "url": data.get('file_url')
            },
            "Status": {
                "select": {
                    "name": "Processed"
                }
            }
        }
        
        # Remove None values (e.g. if Date is missing)
        properties = {k: v for k, v in properties.items() if v is not None}

        try:
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            print(f"Added to Notion: {data.get('vendor')} - {data.get('amount')}")
        except Exception as e:
            print(f"Error adding to Notion: {e}")
