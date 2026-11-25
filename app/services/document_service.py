
import os
from sqlalchemy.orm import Session

from app.models.document import Document



def create_document(
    db: Session,
    filename: str,
    file_path: str,
    source: str = "local_upload"
):
    file_type = os.path.splitext(filename)[1].lower()

    document = Document(
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        source=source,
        status="pending"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document



def get_document_by_id(db: Session, document_id: int):
    return db.query(Document).filter(
        Document.id == document_id
    ).first()


def get_all_documents(db: Session):
    return db.query(Document).order_by(
        Document.id.desc()
    ).all()


def update_document_extraction(
    db: Session,
    document_id: int,
    extracted_text: str,
    metadata: dict | None = None
):
    document = get_document_by_id(db, document_id)

    if document is None:
        return None

    document.extracted_text = extracted_text
    document.metadata_json = metadata
    document.status = "completed"

    db.commit()
    db.refresh(document)

    return document


def update_document_status(
    db: Session,
    document_id: int,
    status: str
):
    document = get_document_by_id(db, document_id)

    if document is None:
        return None

    document.status = status
    db.commit()
    db.refresh(document)

    return document

