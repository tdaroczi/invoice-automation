import pdfplumber
import re
from typing import Dict, Optional

class ExtractionService:
    def extract_data(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """
        Extracts Vendor, Date, and Amount from a PDF invoice.
        Returns a dictionary with keys: 'vendor', 'date', 'amount'.
        """
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return {'vendor': None, 'date': None, 'amount': None}

        return {
            'vendor': self._extract_vendor(text),
            'date': self._extract_date(text),
            'amount': self._extract_amount(text)
        }

    def _extract_date(self, text: str) -> Optional[str]:
        # Regex for common date formats: YYYY.MM.DD, YYYY-MM-DD, DD/MM/YYYY
        # Hungarian format often: 2023.10.25. or 2023. 10. 25.
        date_patterns = [
            r'\b\d{4}\.\s?\d{2}\.\s?\d{2}\.?\b',  # 2023.10.25.
            r'\b\d{4}-\d{2}-\d{2}\b',             # 2023-10-25
            r'\b\d{2}/\d{2}/\d{4}\b'              # 25/10/2023
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        # Look for amounts with currency indicators
        # Patterns: "1 234 Ft", "1.234 HUF", "Total: 1234"
        # We want the largest number usually, or the one near "Total" / "Összesen"
        
        # Simple heuristic: find all numbers followed by Ft or HUF
        # Handle spaces as thousand separators and commas/dots as decimals
        
        # Regex to find number-like strings followed by Ft/HUF
        # Groups: 1=Number part
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
