
from tika import parser

from app.core.config import settings


def extract_document(file_path: str):

    parsed = parser.from_file(
        file_path,
        serverEndpoint=settings.TIKA_SERVER_URL
    )

    metadata = parsed.get("metadata") or {}

    text = (
        parsed.get("content")
        or metadata.get("tk:content")
        or ""
    )

    metadata.pop("tk:content", None)

    return {
        "text": text.strip(),
        "metadata": metadata
    }
