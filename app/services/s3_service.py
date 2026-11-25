
import shutil
from pathlib import Path, PureWindowsPath
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings


def download_file_from_s3(bucket_name: str, file_key: str):

    allowed_extensions = {
        ".pdf", ".docx", ".doc",
        ".txt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".csv"
    }

    max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    filename = Path(file_key.replace("\\", "/")).name

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

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION
    )

    upload_dir = Path("storage/uploads") / uuid4().hex
    local_path = upload_dir / filename

    try:
        object_info = s3.head_object(
            Bucket=bucket_name,
            Key=file_key
        )

        file_size = object_info["ContentLength"]

        if file_size == 0:
            raise ValueError("Empty files are not allowed")

        if file_size > max_file_size:
            raise ValueError(
                f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB"
            )

        upload_dir.mkdir(parents=True, exist_ok=False)

        s3.download_file(
            bucket_name,
            file_key,
            str(local_path)
        )

        actual_size = local_path.stat().st_size

        if actual_size == 0:
            raise ValueError("Empty files are not allowed")

        if actual_size > max_file_size:
            raise ValueError(
                f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB"
            )

        return {
            "filename": filename,
            "file_path": str(local_path),
            "source": "aws_s3"
        }

    except NoCredentialsError:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise RuntimeError(
            "AWS credentials not configured"
        ) from None

    except ClientError:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise RuntimeError(
            "Failed to download document from S3"
        ) from None

    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise
