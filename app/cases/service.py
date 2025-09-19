from sqlalchemy.orm import Session
from app.cases.models import Case, File
from app.opensearch.client import get_opensearch_client, create_case_index
from typing import List, Optional

def create_case(db: Session, name: str, description: str, created_by: int) -> Case:
    case = Case(name=name, description=description, created_by=created_by)
    db.add(case)
    db.commit()
    db.refresh(case)
    
    # Create OpenSearch index for this case
    client = get_opensearch_client()
    create_case_index(client, case.id)
    
    return case

def get_cases(db: Session, limit: int = 5) -> List[Case]:
    return db.query(Case).order_by(Case.created_at.desc()).limit(limit).all()

def get_case_by_id(db: Session, case_id: int) -> Optional[Case]:
    return db.query(Case).filter(Case.id == case_id).first()

def get_case_stats(db: Session, case_id: int) -> dict:
    files = db.query(File).filter(File.case_id == case_id).all()
    total_files = len(files)
    total_size = sum(f.size_bytes for f in files)
    completed_files = len([f for f in files if f.status == "completed"])
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "completed_files": completed_files,
        "processing_files": len([f for f in files if f.status == "processing"]),
        "queued_files": len([f for f in files if f.status == "queued"])
    }

def get_system_stats(db: Session) -> dict:
    total_cases = db.query(Case).count()
    total_files = db.query(File).count()
    total_size = db.query(File).with_entities(File.size_bytes).all()
    total_size_bytes = sum(row[0] for row in total_size if row[0])
    
    return {
        "total_cases": total_cases,
        "total_files": total_files,
        "total_size_bytes": total_size_bytes
    }
