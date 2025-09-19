from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime
from app.db import engine
from app.auth.routes import router as auth_router
from app.auth.routes import current_session as get_session_ctx, role_guard
from app.cases.routes import router as cases_router

APP_NAME = "caseScope"
VERSION = (open(os.path.join(os.path.dirname(__file__), "..", "VERSION")).read().strip()
           if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "VERSION")) else "6.3.0")

app = FastAPI(title=APP_NAME, version=VERSION)
app.include_router(auth_router)
app.include_router(cases_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def get_user_role(request: Request) -> str:
    sess = get_session_ctx(request)
    return (sess or {}).get("role","Anonymous")

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "version": VERSION})

@app.get("/health", response_class=HTMLResponse)
def health(request: Request):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return HTMLResponse(f"OK {now} v{VERSION}")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, role: str = Depends(get_user_role)):
    if role == "Anonymous":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "version": VERSION,
        "username": request.cookies.get("username", "Admin"),
        "role": role
    })

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, role: str = Depends(get_user_role)):
    if role == "Anonymous":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("upload.html", {"request": request, "version": VERSION, "username": request.cookies.get("username"), "role": role})

@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, role: str = Depends(get_user_role)):
    if role == "Anonymous":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("search.html", {"request": request, "version": VERSION, "username": request.cookies.get("username"), "role": role})

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, role: str = Depends(get_user_role)):
    if role == "Anonymous":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("settings.html", {"request": request, "version": VERSION, "username": request.cookies.get("username"), "role": role})

from app.system.health import get_system_info, get_service_versions, get_rules_info
from app.cases.service import get_cases, get_system_stats
from app.cases.models import Case, File
from app.db import SessionLocal

# Create tables
from app.cases.models import Base
Base.metadata.create_all(bind=engine)


from fastapi.responses import JSONResponse

@app.get("/api/dashboard-data", response_class=JSONResponse)
def dashboard_data(request: Request, role: str = Depends(get_user_role)):
    if role == "Anonymous":
        return {"error": "unauthorized"}
    
    with SessionLocal() as db:
        system_stats = get_system_stats(db)
        recent_cases = get_cases(db, 5)
        system_info = get_system_info()
        service_versions = get_service_versions()
        rules_info = get_rules_info()
        
        # OpenSearch health
        from app.opensearch.client import health_check
        opensearch_status = health_check()
        
        return {
            "opensearch_status": opensearch_status["status"],
            "opensearch_version": opensearch_status.get("version", "unknown"),
            "os_version": system_info["os"],
            "hostname": system_info["hostname"],
            "uptime": system_info["uptime"],
            "service_versions": service_versions,
            "sigma_count": rules_info["sigma_count"],
            "sigma_updated": rules_info["sigma_updated"],
            "chainsaw_count": rules_info["chainsaw_count"],
            "chainsaw_updated": rules_info["chainsaw_updated"],
            "case_count": system_stats["total_cases"],
            "file_count": system_stats["total_files"],
            "file_size_bytes": system_stats["total_size_bytes"],
            "recent_cases": [
                {
                    "id": case.id,
                    "name": case.name,
                    "description": case.description,
                    "created_at": case.created_at.isoformat(),
                    "created_by": case.created_by
                }
                for case in recent_cases
            ]
        }
