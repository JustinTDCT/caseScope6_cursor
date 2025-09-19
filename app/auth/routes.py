from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from itsdangerous import TimestampSigner, BadSignature
from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.auth.service import get_user_by_username, verify_password, update_last_login, change_password
from app.auth.service import ensure_default_admin
from app.auth.models import User
from datetime import timedelta
import os
from app.auth.audit import log_login, log_logout

router = APIRouter()
SECRET = os.environ.get("SESSION_SECRET", "CHANGE_ME_SECRET")
signer = TimestampSigner(SECRET)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_default_admin(db)

def set_session(resp: RedirectResponse, username: str, role: str):
    cookie = f"{username}|{role}"
    token = signer.sign(cookie.encode()).decode()
    resp.set_cookie("session", token, httponly=True, samesite="lax", max_age=int(timedelta(days=7).total_seconds()))

def clear_session(resp: RedirectResponse):
    resp.delete_cookie("session")

def get_session(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        raw = signer.unsign(token.encode(), max_age=int(timedelta(days=7).total_seconds())).decode()
        username, role = raw.split("|", 1)
        return {"username": username, "role": role}
    except BadSignature:
        return None

def require_role(*allowed_roles: str):
    def dep(request: Request):
        sess = get_session(request)
        if not sess or sess["role"] not in allowed_roles:
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        return sess
    return dep

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/", status_code=302)
    update_last_login(db, user)
    try:
        ip = os.environ.get('FORWARDED_FOR','') or ''
        log_login(user.username, ip, '', os.uname().nodename)
    except Exception:
        pass
    resp = RedirectResponse(url="/dashboard" if not user.must_change_password else "/account", status_code=302)
    set_session(resp, user.username, user.role)
    return resp

@router.post("/logout")
def logout():
    try:
        ip = ''
        log_logout('unknown', ip, '', os.uname().nodename)
    except Exception:
        pass
    resp = RedirectResponse(url="/", status_code=302)
    clear_session(resp)
    return resp

@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
    return templates.TemplateResponse("account.html", {"request": request})

@router.post("/account/change-password")
def account_change_password(request: Request, new_password: str = Form(...), db: Session = Depends(get_db)):
    sess = get_session(request)
    if not sess:
        return RedirectResponse(url="/", status_code=302)
    user = get_user_by_username(db, sess["username"])
    if not user:
        return RedirectResponse(url="/", status_code=302)
    change_password(db, user, new_password)
    resp = RedirectResponse(url="/dashboard", status_code=302)
    return resp

# Expose helpers for main.py
def current_session(request: Request):
    return get_session(request)

def role_guard(*roles: str):
    return require_role(*roles)
