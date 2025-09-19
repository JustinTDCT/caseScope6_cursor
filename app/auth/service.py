from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime
from app.auth.models import User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def ensure_default_admin(db: Session) -> None:
    if not get_user_by_username(db, "Admin"):
        u = User(
            username="Admin",
            password_hash=hash_password("ChangeMe!"),
            role="Admin",
            must_change_password=1
        )
        db.add(u)
        db.commit()

def update_last_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()

def change_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    user.must_change_password = 0
    db.add(user)
    db.commit()
