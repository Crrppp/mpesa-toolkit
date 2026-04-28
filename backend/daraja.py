# backend/daraja.py
import requests
import base64
from config import DARAA_CONSUMER_KEY, DARAA_CONSUMER_SECRET, DARAA_BASE_URL
from cryptography.fernet import Fernet
import os

FERNET_KEY = os.getenv("FERNET_KEY", "")

def get_access_token(consumer_key=None, consumer_secret=None):
    key = consumer_key or DARAA_CONSUMER_KEY
    secret = consumer_secret or DARAA_CONSUMER_SECRET
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    url = f"{DARAA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    headers = {"Authorization": f"Basic {auth}"}
    res = requests.get(url, headers=headers).json()
    return res.get("access_token")

def register_c2b_urls(shortcode, conf_url, val_url, consumer_key=None, consumer_secret=None):
    token = get_access_token(consumer_key, consumer_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"ShortCode": shortcode, "ResponseType": "Completed", "ConfirmationURL": conf_url, "ValidationURL": val_url}
    return requests.post(f"{DARAA_BASE_URL}/mpesa/c2b/v1/registerurl", json=payload, headers=headers).json()

def transaction_status(transaction_id, consumer_key=None, consumer_secret=None):
    token = get_access_token(consumer_key, consumer_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"TransactionID": transaction_id}
    return requests.post(f"{DARAA_BASE_URL}/mpesa/transactionstatus/v1/query", json=payload, headers=headers).json()

def b2c_payment(amount, phone, shortcode, initiator, security_cred,
                consumer_key=None, consumer_secret=None, result_url="", timeout_url=""):
    token = get_access_token(consumer_key, consumer_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "InitiatorName": initiator,
        "SecurityCredential": security_cred,
        "CommandID": "BusinessPayment",
        "Amount": str(amount),
        "PartyA": shortcode,
        "PartyB": phone,
        "Remarks": "Payment",
        "QueueTimeOutURL": timeout_url or "https://example.com/timeout",
        "ResultURL": result_url or "https://example.com/result",
        "Occasion": "Payment"
    }
    return requests.post(f"{DARAA_BASE_URL}/mpesa/b2c/v1/paymentrequest", json=payload, headers=headers).json()

def encrypt_credentials(plain_text):
    if not FERNET_KEY:
        raise Exception("FERNET_KEY not set")
    f = Fernet(FERNET_KEY)
    return f.encrypt(plain_text.encode()).decode()

def decrypt_credentials(encrypted_text):
    f = Fernet(FERNET_KEY)
    return f.decrypt(encrypted_text.encode()).decode()