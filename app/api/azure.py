
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.azure_service import download_file_from_azure
from app.services.document_service import create_document
from app.tasks.document_tasks import process_document_task


router = APIRouter(
    prefix="/azure",
    tags=["Azure Blob Storage"]
)


class AzureImportRequest(BaseModel):
    container_name: str
    blob_name: str


@router.post("/import")
def import_document_from_azure(
    request: AzureImportRequest,
    db: Session = Depends(get_db)
):
    try:
        # Download document from Azure Blob Storage
        file_info = download_file_from_azure(
            container_name=request.container_name,
            blob_name=request.blob_name
        )

        # Create document record in PostgreSQL
        
        document = create_document(
            db=db,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            source="azure_blob"
        )

        # Submit document to Celery
        task = process_document_task.delay(document.id)

        return {
            "message": "Document imported from Azure Blob Storage",
            "document_id": document.id,
            "filename": document.filename,
            "source": "azure_blob",
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

