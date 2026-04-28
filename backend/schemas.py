# backend/schemas.py
from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    business_name: str
    account_number: str
    password: str

class LoginRequest(BaseModel):
    business_name: str
    password: str

class B2CRequest(BaseModel):
    phone_number: str
    amount: float

class DarajaKeysRequest(BaseModel):
    consumer_key: str
    consumer_secret: str