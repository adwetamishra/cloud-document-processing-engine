
from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.processing_service import process_document
from app.services.document_service import update_document_status


@celery_app.task(name="process_document_task")
def process_document_task(document_id: int):
    db = SessionLocal()

    try:
        # Mark the document as processing
        update_document_status(db, document_id, "processing")

        # Extract text and save it to PostgreSQL
        result = process_document(db, document_id)

        return result

    except Exception:
        db.rollback()

        # Mark the document as failed if an error occurs
        update_document_status(db, document_id, "failed")
        raise

    finally:
        db.close()
