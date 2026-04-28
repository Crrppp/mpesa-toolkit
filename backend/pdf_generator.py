# backend/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_statement_pdf(transactions, business_name, date_range=""):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h-50, f"Statement - {business_name}")
    p.setFont("Helvetica", 12)
    p.drawString(50, h-70, f"Period: {date_range}")
    y = h - 100
    for t in transactions[:100]:  # Limit
        line = f"{t.timestamp.strftime('%Y-%m-%d %H:%M')}  {t.transaction_type}  KES {t.amount:,.2f}  {t.phone_number}"
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = h - 50
    p.save()
    buffer.seek(0)
    return buffer