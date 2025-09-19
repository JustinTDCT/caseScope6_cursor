from fastapi import APIRouter, Request, Form, Depends, status, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.files.service import save_uploaded_file, get_files_for_case, rerun_rules_for_file, reindex_file
from app.auth.routes import current_session as get_session_ctx
from app.auth.audit import log_audit
from fastapi.templating import Jinja2Templates
import os
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
VERSION = (open(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")).read().strip() if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")) else "6.6.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/upload")
def upload_form(request: Request, case: int = None):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "selected_case": case,
        "version": VERSION
    })

@router.post("/upload")
def upload_files(request: Request, files: List[UploadFile] = Form(...), case_id: int = Form(...), db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return {"error": "unauthorized"}
    
    if len(files) > 5:
        return {"error": "Maximum 5 files allowed"}
    
    uploaded_files = []
    for file in files:
        if file.filename and file.filename.endswith('.evtx'):
            file_content = file.file.read()
            file_record = save_uploaded_file(file_content, file.filename, case_id, sess.get("user_id"), db)
            uploaded_files.append({
                "id": file_record.id,
                "filename": file_record.filename,
                "status": file_record.status
            })
            log_audit(sess.get("username"), "upload_file", f"Uploaded {file.filename} to case {case_id}")
    
    return {"success": True, "files": uploaded_files}

@router.get("/files/{case_id}")
def files_list(request: Request, case_id: int, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    files = get_files_for_case(db, case_id)
    return templates.TemplateResponse("files_list.html", {
        "request": request,
        "files": files,
        "case_id": case_id,
        "version": VERSION
    })

@router.post("/files/{file_id}/rerun-rules")
def rerun_rules(request: Request, file_id: int, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return {"error": "unauthorized"}
    
    success = rerun_rules_for_file(file_id, db)
    log_audit(sess.get("username"), "rerun_rules", f"Re-ran rules for file {file_id}")
    
    return {"success": success}

@router.post("/files/{file_id}/reindex")
def reindex(request: Request, file_id: int, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return {"error": "unauthorized"}
    
    success = reindex_file(file_id, db)
    log_audit(sess.get("username"), "reindex_file", f"Re-indexed file {file_id}")
    
    return {"success": success}

@router.get("/api/files/{case_id}")
def api_files_list(request: Request, case_id: int, db: Session = Depends(get_db)):
    sess = get_session_ctx(request)
    if not sess:
        return {"error": "unauthorized"}
    
    files = get_files_for_case(db, case_id)
    return {"files": [
        {
            "id": f.id,
            "filename": f.filename,
            "size_bytes": f.size_bytes,
            "status": f.status,
            "progress": f.progress,
            "uploaded_at": f.uploaded_at.isoformat(),
            "events_ingested": f.events_ingested or 0,
            "detections_found": f.detections_found or 0
        }
        for f in files
    ]}
