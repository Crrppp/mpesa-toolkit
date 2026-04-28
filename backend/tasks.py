# backend/tasks.py
from celery_app import celery_app
from pdf_parser import parse_mpesa_statement
from database import SessionLocal
from models import Transaction

@celery_app.task(bind=True)
def process_pdf_statement(self, business_id: int, pdf_bytes: bytes, password: str):
    """Process uploaded M-Pesa statement PDF, inserting transactions."""
    self.update_state(state='PROGRESS', meta={'progress': 10})
    try:
        transactions = parse_mpesa_statement(pdf_bytes, password)
        self.update_state(state='PROGRESS', meta={'progress': 50})
        db = SessionLocal()
        imported = 0
        for txn in transactions:
            existing = db.query(Transaction).filter(Transaction.transaction_id == txn["transaction_id"]).first()
            if existing:
                continue
            new_txn = Transaction(
                business_id=business_id,
                transaction_type="C2B" if txn["amount"] < 0 else "B2C",
                transaction_id=txn["transaction_id"],
                amount=abs(txn["amount"]),
                phone_number=txn["phone_number"],
                sender_name=txn.get("sender_name"),
                account_reference=txn["description"],
                timestamp=txn["date"],
                status="Completed"
            )
            db.add(new_txn)
            imported += 1
        db.commit()
        db.close()
        return {"status": "success", "imported": imported}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise