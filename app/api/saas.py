
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.saas_service import download_file_from_saas
from app.services.document_service import create_document
from app.tasks.document_tasks import process_document_task


router = APIRouter(
    prefix="/saas",
    tags=["SaaS API"]
)


class SaaSImportRequest(BaseModel):
    file_url: str


@router.post("/import")
def import_document_from_saas(
    request: SaaSImportRequest,
    db: Session = Depends(get_db)
):
    try:
        # Download document from SaaS API
        file_info = download_file_from_saas(
            file_url=request.file_url
        )

        # Register document in PostgreSQL
        
        document = create_document(
            db=db,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            source="saas_api"
        )


        # Submit document for background processing
        task = process_document_task.delay(document.id)

        return {
            "message": "Document imported from SaaS API",
            "document_id": document.id,
            "filename": document.filename,
            "source": "saas_api",
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

