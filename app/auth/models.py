from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), nullable=False, default="Analyst")  # Admin|Analyst|ReadOnly
    must_change_password = Column(Integer, nullable=False, default=0)  # 1=true, 0=false
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)
