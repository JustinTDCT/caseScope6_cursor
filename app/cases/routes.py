from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.cases.service import create_case, get_cases, get_case_by_id, get_case_stats
from app.cases.models import Case
from app.auth.routes import current_session as get_session_ctx
from app.auth.audit import log_audit
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/cases", response_class=HTMLResponse)
def cases_list(request: Request, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    cases = get_cases(db, 50)  # Get more cases for the list page
    return templates.TemplateResponse("cases_list.html", {
        "request": request,
        "cases": cases,
        "username": sess.get("username"),
        "role": sess.get("role")
    })

@router.get("/cases/new", response_class=HTMLResponse)
def new_case_form(request: Request):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("case_form.html", {
        "request": request,
        "case": None,
        "username": sess.get("username"),
        "role": sess.get("role")
    })

@router.post("/cases", response_class=RedirectResponse)
def create_new_case(request: Request, 
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Get user ID from session (you'll need to add this to your session)
    user_id = 1  # For now, assume Admin user ID is 1
    
    case = create_case(db, name, description, user_id)
    log_audit(sess.get("username"), "create_case", f"Created case: {name}")
    
    return RedirectResponse(url=f"/cases/{case.id}", status_code=status.HTTP_302_FOUND)

@router.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail(request: Request, case_id: int, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    case = get_case_by_id(db, case_id)
    if not case:
        return RedirectResponse(url="/cases", status_code=status.HTTP_302_FOUND)
    
    stats = get_case_stats(db, case_id)
    return templates.TemplateResponse("case_detail.html", {
        "request": request,
        "case": case,
        "stats": stats,
        "username": sess.get("username"),
        "role": sess.get("role")
    })

@router.get("/api/cases", response_class=JSONResponse)
def api_cases_list(request: Request, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return {"error": "unauthorized"}
    
    cases = get_cases(db, 50)
    return {
        "cases": [
            {
                "id": case.id,
                "name": case.name,
                "description": case.description,
                "created_at": case.created_at.isoformat(),
                "created_by": case.created_by
            }
            for case in cases
        ]
    }
