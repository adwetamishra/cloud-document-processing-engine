
import shutil

from pathlib import Path, PureWindowsPath
from uuid import uuid4
from urllib.parse import urlparse, unquote

import httpx


def download_file_from_saas(file_url: str):

    allowed_extensions = {
        ".pdf", ".docx", ".doc",
        ".txt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".csv"
    }

    max_file_size = 50 * 1024 * 1024

    parsed_url = urlparse(file_url)

    # Restrict access to the local SaaS server
    if (
        parsed_url.scheme != "http"
        or parsed_url.hostname != "127.0.0.1"
        or parsed_url.port != 8001
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ValueError(
            "Only the local SaaS API is allowed."
        )

    # Validate filename
    filename = Path(
        unquote(parsed_url.path).replace("\\", "/")
    ).name

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

    # Validate file extension
    if Path(filename).suffix.lower() not in allowed_extensions:
        raise ValueError("Unsupported file format")

    # Generate unique storage directory
    upload_dir = Path("storage/uploads") / uuid4().hex
    local_path = upload_dir / filename

    try:
        with httpx.stream(
            "GET",
            file_url,
            timeout=30.0,
            follow_redirects=False,
            trust_env=False
        ) as response:

            response.raise_for_status()

            # Check declared file size
            content_length = response.headers.get(
                "content-length"
            )

            if content_length is not None:
                if int(content_length) > max_file_size:
                    raise ValueError(
                        "File size exceeds 50 MB"
                    )

            upload_dir.mkdir(
                parents=True,
                exist_ok=False
            )

            downloaded_size = 0

            # Stream the document in chunks
            with open(local_path, "wb") as file:

                for chunk in response.iter_bytes(
                    chunk_size=65536
                ):
                    downloaded_size += len(chunk)

                    if downloaded_size > max_file_size:
                        raise ValueError(
                            "File size exceeds 50 MB"
                        )

                    file.write(chunk)

            if downloaded_size == 0:
                raise ValueError(
                    "Empty files are not allowed"
                )

        return {
            "filename": filename,
            "file_path": str(local_path),
            "source": "saas_api"
        }

    except httpx.HTTPError:
        shutil.rmtree(
            upload_dir,
            ignore_errors=True
        )

        raise RuntimeError(
            "Failed to download document from SaaS API"
        ) from None

    except Exception:
        shutil.rmtree(
            upload_dir,
            ignore_errors=True
        )
        raise
