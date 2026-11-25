import os
from pathlib import Path
from uuid import uuid4
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.services.processing_service import process_document
from app.tasks.document_tasks import process_document_task
from app.celery_app import celery_app
from app.db.database import get_db
from app.services.document_service import (
    create_document,
    get_document_by_id,
    get_all_documents
)
from app.schemas.document import DocumentUploadResponse
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])



@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Supported file formats
    allowed_extensions = {
        ".pdf", ".docx", ".doc",
        ".txt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".csv"
    }

    # Maximum file size: 50 MB
    max_file_size = 50 * 1024 * 1024

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    filename = Path(
        file.filename.replace("\\", "/")
    ).name

    if (
        not filename
        or filename in (".", "..")
        or len(filename) > 255
        or any(c in filename for c in '<>:"/\\|?*')
        or any(ord(c) < 32 for c in filename)
        or filename.endswith((" ", "."))
        or Path(filename).is_reserved()
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    # Validate file extension
    file_extension = Path(filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file format"
        )

    # Validate file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty files are not allowed"
        )

    if file_size > max_file_size:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 50 MB"
        )

    # Create a unique storage directory
    upload_dir = Path("storage/uploads") / uuid4().hex
    file_path = upload_dir / filename

    try:
        upload_dir.mkdir(parents=True, exist_ok=False)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = create_document(
            db=db,
            filename=filename,
            file_path=str(file_path),
            source="local_upload"
        )

    except Exception:
        db.rollback()
        shutil.rmtree(upload_dir, ignore_errors=True)

        raise HTTPException(
            status_code=500,
            detail="Document upload failed"
        )

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status
    }

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document
@router.get("/", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return get_all_documents(db)
@router.get("/{document_id}/text")
def get_document_text(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "extracted_text": document.extracted_text
    }

@router.post("/{document_id}/process")
def process_uploaded_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    result = process_document(db, document_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "message": "Document processed successfully",
        **result
    }

@router.post("/{document_id}/process-async")
def process_document_async(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    task = process_document_task.delay(document_id)

    return {
        "message": "Document processing started",
        "document_id": document_id,
        "task_id": task.id,
        "task_status": task.status
    }

@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str):
    task = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task.id,
        "status": task.status
    }

    if task.successful():
        response["result"] = task.result

    elif task.failed():
        response["error"] = str(task.result)

    return response

@router.get("/{document_id}/metadata")
def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = get_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "metadata": document.metadata_json
    }
