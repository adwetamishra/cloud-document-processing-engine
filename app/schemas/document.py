
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str | None = None
    source: str
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    status: str
