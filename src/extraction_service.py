import pdfplumber
import re
from typing import Dict, Optional

class ExtractionService:
    def extract_data(self, pdf_path):
        """
        Extracts key data from the PDF invoice.
        Returns a dictionary with:
        - type (Számla / Díjbekérő)
        - invoice_number
        - vendor
        - vendor_tax_id
        - issue_date
        - due_date
        - amount
        - buyer
        """
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return {}

        data = {
            "type": "Számla", # Default
            "invoice_number": "",
            "vendor": "",
            "vendor_tax_id": "",
            "issue_date": "",
            "due_date": "",
            "amount": "",
            "buyer": "",
            "comment": ""
        }

        amount_pattern = r'([\d\s\.,]+)\s*(?:Ft|HUF)'
        matches = re.findall(amount_pattern, text, re.IGNORECASE)
        
        amounts = []
        for m in matches:
            # Clean the number: remove spaces, replace decimal separator
            clean_num = m.replace(' ', '')
            # If it has a comma, replace with dot (Hungarian standard: 1234,56 -> 1234.56)
            # But if it has multiple dots, it might be 1.234.567 -> 1234567
            
            if ',' in clean_num:
                clean_num = clean_num.replace('.', '').replace(',', '.')
            else:
                # If only dots, check if it's a thousand separator or decimal
                # 1.234 -> 1234; 12.34 -> 12.34
                # This is ambiguous without context. Let's assume dot is thousand sep if followed by 3 digits?
                # For simplicity, let's assume integers for now if no comma.
                pass
            
            try:
                amounts.append(float(clean_num))
            except ValueError:
                continue
                
        if amounts:
            return max(amounts) # Assumption: Invoice total is the largest amount
        return None

    def _extract_vendor(self, text: str) -> Optional[str]:
        # Very naive: First non-empty line?
        # Or look for "Szállító:" / "Vendor:"
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            return lines[0] # Return first line as vendor guess
        return "Unknown Vendor"
