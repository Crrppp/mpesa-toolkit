# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    account_number = Column(String, index=True)  # Till/Paybill
    is_active = Column(Boolean, default=True)
    daraja_consumer_key_encrypted = Column(Text, nullable=True)
    daraja_consumer_secret_encrypted = Column(Text, nullable=True)
    users = relationship("User", back_populates="business")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    username = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String, default="cashier")  # owner, admin, accountant, cashier
    business = relationship("Business", back_populates="users")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    transaction_type = Column(String)  # C2B, B2C
    transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    phone_number = Column(String)
    sender_name = Column(String, nullable=True)
    account_reference = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Completed")