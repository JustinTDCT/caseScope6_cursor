from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime

APP_NAME = "caseScope"
VERSION = (open(os.path.join(os.path.dirname(__file__), "..", "VERSION")).read().strip()
           if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "VERSION")) else "6.0.0")

app = FastAPI(title=APP_NAME, version=VERSION)

from app.auth.routes import router as auth_router
app.include_router(auth_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def get_user_role(request: Request) -> str:
    return request.cookies.get("role", "Anonymous")

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "version": VERSION})

@app.get("/health", response_class=HTMLResponse)
def health(request: Request):
    # Stub health; installer will connect OpenSearch and more
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
