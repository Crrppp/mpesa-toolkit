# backend/pdf_parser.py
import PyPDF2
import re
from io import BytesIO
from datetime import datetime

def parse_mpesa_statement(pdf_bytes, password):
    """Extract transactions from M-Pesa PDF statement. Returns list of dicts."""
    reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
    if reader.is_encrypted:
        reader.decrypt(password)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    # Pattern: date (YYYY-MM-DD HH:MM:SS) description amount balance
    pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    transactions = []
    for match in matches:
        date_str, description, amount_str, balance_str = match
        amount = float(amount_str.replace(',', ''))
        balance = float(balance_str.replace(',', ''))
        transaction_id = f"PDF_{date_str.replace(' ','T').replace(':','')}_{hash(description)}"
        phone_match = re.search(r'254\d{9}', description)
        phone = phone_match.group(0) if phone_match else ""
        name_match = re.search(r'([A-Z\s]+)\s+254', description)
        name = name_match.group(1).strip() if name_match else ""
        transactions.append({
            "date": datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"),
            "description": description,
            "amount": amount,
            "balance": balance,
            "transaction_id": transaction_id,
            "phone_number": phone,
            "sender_name": name
        })
    return transactions