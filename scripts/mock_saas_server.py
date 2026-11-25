
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


app = FastAPI(
    title="Mock SaaS Document Provider",
    version="1.0.0"
)

DOCUMENT_PATH = (
    Path(__file__).resolve().parent.parent
    / "samples"
    / "sample.txt"
)


@app.get("/")
def home():
    return {
        "message": "Mock SaaS API is running",
        "status": "success"
    }


@app.get("/documents")
def list_documents():
    return {
        "documents": [
            {
                "id": 1,
                "filename": "sample.txt",
                "download_url": (
                    "http://127.0.0.1:8001/documents/sample.txt"
                )
            }
        ]
    }


@app.get("/documents/sample.txt")
def download_document():

    if not DOCUMENT_PATH.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return FileResponse(
        path=DOCUMENT_PATH,
        filename="sample.txt",
        media_type="text/plain"
    )
