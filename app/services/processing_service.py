
from sqlalchemy.orm import Session

from app.services.document_service import (
    get_document_by_id,
    update_document_extraction
)
from app.services.extraction_service import extract_document


def process_document(db: Session, document_id: int):
    # Step 1: Find the document
    document = get_document_by_id(db, document_id)

    if document is None:
        return None

    # Step 2: Extract text and metadata using Apache Tika
    result = extract_document(document.file_path)

    # Step 3: Save text and metadata in PostgreSQL
    updated_document = update_document_extraction(
        db=db,
        document_id=document_id,
        extracted_text=result["text"],
        metadata=result["metadata"]
    )

    # Step 4: Return the processing result
    return {
        "document_id": updated_document.id,
        "filename": updated_document.filename,
        "status": updated_document.status,
        "text_length": len(updated_document.extracted_text),
        "metadata": updated_document.metadata_json
    }
