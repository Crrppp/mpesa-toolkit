# backend/app.py - FULL CORRECTED VERSION
from fastapi import FastAPI, Depends, HTTPException, File, Form, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
import logging
import os
from jose import jwt  # FIXED: was "import jwt"

from database import engine, get_db, Base
import models
import schemas
from auth import *
from daraja import transaction_status, encrypt_credentials, decrypt_credentials, b2c_payment
from tasks import process_pdf_statement
from celery.result import AsyncResult
from pdf_generator import generate_statement_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="M-Pesa Business Toolkit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

METABASE_SITE_URL = os.getenv("METABASE_SITE_URL", "http://localhost:3000")
METABASE_SECRET_KEY = os.getenv("METABASE_SECRET_KEY", "change-me")

logging.basicConfig(level=logging.INFO)

# ---------- Auth ----------
@app.post("/api/auth/register")
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.Business).filter(models.Business.name == req.business_name).first():
        raise HTTPException(400, "Business already registered")
    biz = models.Business(name=req.business_name, account_number=req.account_number)
    db.add(biz)
    db.flush()
    hashed = get_password_hash(req.password)
    user = models.User(business_id=biz.id, username=req.business_name+"_owner", password_hash=hashed, role="owner")
    db.add(user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/api/auth/login")
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    biz = db.query(models.Business).filter(models.Business.name == req.business_name).first()
    if not biz:
        raise HTTPException(401, "Invalid credentials")
    user = db.query(models.User).filter(models.User.business_id == biz.id).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"user_id": user.id, "business_id": biz.id, "role": user.role})
    return {"access_token": token, "user": {"id": user.id, "business_name": biz.name, "role": user.role}}

@app.get("/api/auth/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "business_name": current_user.business.name, "role": current_user.role}

# ---------- Transactions ----------
@app.get("/api/transactions")
def get_transactions(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(models.Transaction).filter(models.Transaction.business_id == current_user.business_id)
    if from_date:
        q = q.filter(models.Transaction.timestamp >= from_date)
    if to_date:
        q = q.filter(models.Transaction.timestamp <= to_date)
    return q.order_by(models.Transaction.timestamp.desc()).limit(500).all()

@app.get("/api/statements/pdf")
def download_pdf(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(models.Transaction).filter(models.Transaction.business_id == current_user.business_id)
    if from_date:
        q = q.filter(models.Transaction.timestamp >= from_date)
    if to_date:
        q = q.filter(models.Transaction.timestamp <= to_date)
    txns = q.all()
    buffer = generate_statement_pdf(txns, current_user.business.name, f"{from_date} to {to_date}")
    return Response(content=buffer.read(), media_type="application/pdf")

# ---------- Statement Upload ----------
@app.post("/api/statements/upload")
async def upload_statement(
    file: UploadFile = File(...),
    password: str = Form(...),
    current_user: models.User = Depends(get_current_user)
):
    pdf_bytes = await file.read()
    task = process_pdf_statement.delay(current_user.business_id, pdf_bytes, password)
    return {"task_id": task.id}

@app.get("/api/tasks/{task_id}")
def task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == 'PROGRESS':
        return {"state": task.state, "progress": task.info.get('progress', 0)}
    elif task.state == 'SUCCESS':
        return {"state": task.state, "result": task.result}
    elif task.state == 'FAILURE':
        return {"state": task.state, "error": str(task.result)}
    return {"state": task.state, "progress": 0}

# ---------- Daraja Keys ----------
@app.post("/api/business/daraja-keys")
def save_daraja_keys(req: schemas.DarajaKeysRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = current_user.business
    biz.daraja_consumer_key_encrypted = encrypt_credentials(req.consumer_key)
    biz.daraja_consumer_secret_encrypted = encrypt_credentials(req.consumer_secret)
    db.commit()
    return {"message": "Keys saved securely"}

# ---------- B2C Send Money ----------
@app.post("/api/b2c/send")
def send_money(req: schemas.B2CRequest, current_user: models.User = Depends(require_role(["owner", "admin"])), db: Session = Depends(get_db)):
    biz = current_user.business
    if not biz.daraja_consumer_key_encrypted or not biz.daraja_consumer_secret_encrypted:
        raise HTTPException(400, "Please save your Daraja API keys in Settings first")
    ck = decrypt_credentials(biz.daraja_consumer_key_encrypted)
    cs = decrypt_credentials(biz.daraja_consumer_secret_encrypted)
    resp = b2c_payment(req.amount, req.phone_number, "600000", "testapi", "your_cred", ck, cs)
    txn = models.Transaction(business_id=biz.id, transaction_type="B2C", transaction_id=resp.get("ConversationID", "N/A"), amount=req.amount, phone_number=req.phone_number, status="Initiated")
    db.add(txn)
    db.commit()
    return resp

# ---------- Transaction Status ----------
@app.get("/api/transaction-status/{trans_id}")
def check_status(trans_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = current_user.business
    if biz.daraja_consumer_key_encrypted and biz.daraja_consumer_secret_encrypted:
        ck = decrypt_credentials(biz.daraja_consumer_key_encrypted)
        cs = decrypt_credentials(biz.daraja_consumer_secret_encrypted)
        return transaction_status(trans_id, ck, cs)
    return transaction_status(trans_id)

# ---------- Metabase SSO ----------
@app.get("/api/metabase/sso")
def metabase_sso(current_user: models.User = Depends(get_current_user)):
    payload = {"resource": {"dashboard": 1}, "params": {"business_id": current_user.business_id}, "exp": datetime.utcnow().timestamp() + 600}
    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"
    return {"iframe_url": iframe_url}

# ---------- C2B Callbacks ----------
@app.post("/mpesa/c2b/confirmation")
async def c2b_confirmation(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    trans_id = data.get("TransID")
    amount = float(data.get("TransAmount", 0))
    phone = data.get("MSISDN")
    name = data.get("FirstName")
    bill_ref = data.get("BillRefNumber")
    biz = db.query(models.Business).filter(models.Business.account_number == bill_ref).first()
    if biz:
        txn = models.Transaction(business_id=biz.id, transaction_type="C2B", transaction_id=trans_id, amount=amount, phone_number=phone, sender_name=name, account_reference=bill_ref, status="Completed")
        db.add(txn)
        db.commit()
    return {"ResultCode": 0, "ResultDesc": "Success"}

@app.post("/mpesa/c2b/validation")
async def c2b_validation():
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@app.get("/")
def root():
    return {"status": "ok", "message": "M-Pesa Business Toolkit API is running"}