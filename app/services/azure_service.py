
import shutil

from pathlib import Path, PureWindowsPath
from uuid import uuid4

from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

from app.core.config import settings


def download_file_from_azure(
    container_name: str,
    blob_name: str
):

    allowed_extensions = {
        ".pdf", ".docx", ".doc",
        ".txt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".csv"
    }

    max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    filename = Path(blob_name.replace("\\", "/")).name

    if (
        not filename
        or filename in (".", "..")
        or len(filename) > 255
        or any(c in filename for c in '<>:"/\\|?*')
        or any(ord(c) < 32 for c in filename)
        or filename.endswith((" ", "."))
        or PureWindowsPath(filename).is_reserved()
    ):
        raise ValueError("Invalid filename")

    if Path(filename).suffix.lower() not in allowed_extensions:
        raise ValueError("Unsupported file format")

    client = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    )

    blob_client = client.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    upload_dir = Path("storage/uploads") / uuid4().hex
    local_path = upload_dir / filename

    try:
        properties = blob_client.get_blob_properties()
        file_size = properties.size

        if file_size == 0:
            raise ValueError("Empty files are not allowed")

        if file_size > max_file_size:
            raise ValueError(
                f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB"
            )

        upload_dir.mkdir(parents=True, exist_ok=False)

        downloaded_size = 0

        with open(local_path, "wb") as file:
            downloader = blob_client.download_blob()

            for chunk in downloader.chunks():
                downloaded_size += len(chunk)

                if downloaded_size > max_file_size:
                    raise ValueError(
                        f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB"
                    )

                file.write(chunk)

        if downloaded_size == 0:
            raise ValueError("Empty files are not allowed")

        return {
            "filename": filename,
            "file_path": str(local_path),
            "source": "azure_blob"
        }

    except AzureError:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise RuntimeError(
            "Failed to download document from Azure Blob Storage"
        ) from None

    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise
