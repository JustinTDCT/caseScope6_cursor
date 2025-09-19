from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import SessionLocal
from app.cases.models import Case, File
from app.auth.models import User

def create_case(db: Session, name: str, description: str, created_by: int) -> Case:
    case = Case(
        name=name,
        description=description,
        created_by=created_by
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

def get_cases(db: Session, limit: int = None) -> list:
    if limit:
        return db.query(Case).order_by(Case.created_at.desc()).limit(limit).all()
    return db.query(Case).order_by(Case.created_at.desc()).all()

def get_case_by_id(db: Session, case_id: int):
    return db.query(Case).filter(Case.id == case_id).first()

def get_case_stats(db: Session, case_id: int):
    # Refresh the case summary table
    from sqlalchemy import func
    from app.cases.models import File
    
    # Update case summary
    total_files = db.query(File).filter(File.case_id == case_id).count()
    total_events = db.query(func.sum(File.events_ingested)).filter(File.case_id == case_id, File.status == "completed").scalar() or 0
    total_detections = db.query(func.sum(File.detections_found)).filter(File.case_id == case_id, File.status == "completed").scalar() or 0
    
    # Update case summary table
    db.execute(
        "INSERT OR REPLACE INTO case_summary (case_id, total_files, total_events, total_detections, last_updated) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (case_id, total_files, total_events, total_detections)
    )
    db.commit()

    case_files = db.query(File).filter(File.case_id == case_id).all()
    total_size_bytes = sum(f.size_bytes for f in case_files)
    
    return {
        "total_files": len(case_files),
        "total_size_bytes": total_size_bytes,
        "total_events": total_events,
        "total_detections": total_detections,
    }

def get_system_stats(db: Session) -> dict:
    total_cases = db.query(Case).count()
    total_files = db.query(File).count()
    total_size_bytes = db.query(func.sum(File.size_bytes)).filter(File.status == "completed").scalar() or 0
    
    return {
        "total_cases": total_cases,
        "total_files": total_files,
        "total_size_bytes": total_size_bytes,
    }
