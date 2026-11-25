
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.s3_service import download_file_from_s3
from app.services.document_service import create_document
from app.tasks.document_tasks import process_document_task


router = APIRouter(prefix="/s3", tags=["AWS S3"])


class S3ImportRequest(BaseModel):
    bucket_name: str
    file_key: str


@router.post("/import")
def import_document_from_s3(
    request: S3ImportRequest,
    db: Session = Depends(get_db)
):
    try:
        # Download document from AWS S3
        file_info = download_file_from_s3(
            bucket_name=request.bucket_name,
            file_key=request.file_key
        )

        # Save document information in PostgreSQL
        
        document = create_document(
            db=db,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            source="aws_s3"
        )


        # Send document to Celery for background processing
        task = process_document_task.delay(document.id)

        return {
            "message": "Document imported from AWS S3",
            "document_id": document.id,
            "filename": document.filename,
            "source": "aws_s3",
            "task_id": task.id,
            "status": "pending"
        }

    
    except ValueError as error:
        db.rollback()

        message = str(error)

        if message == "Unsupported file format":
            status_code = 415

        elif message == "File size exceeds 50 MB":
            status_code = 413

        elif message in (
            "Invalid filename",
            "Empty files are not allowed",
            "Only the local SaaS API is allowed."
        ):
            status_code = 400

        else:
            status_code = 400
            message = "Invalid import request"

        raise HTTPException(
            status_code=status_code,
            detail=message
        ) from None

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Document import failed"
        ) from None

