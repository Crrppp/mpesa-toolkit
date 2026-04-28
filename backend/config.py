# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mpesa_toolkit.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
FERNET_KEY = os.getenv("FERNET_KEY", "change-me-32-bytes-fernet-key-here==")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# Daraja defaults (sandbox)
DARAA_CONSUMER_KEY = os.getenv("DARAA_CONSUMER_KEY", "")
DARAA_CONSUMER_SECRET = os.getenv("DARAA_CONSUMER_SECRET", "")
DARAA_BASE_URL = os.getenv("DARAA_BASE_URL", "https://sandbox.safaricom.co.ke")
SHORTCODE = os.getenv("SHORTCODE", "174379")
PASSKEY = os.getenv("PASSKEY", "")