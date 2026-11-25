
from pathlib import Path

import boto3
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError

SAMPLE_PATH = (
    Path(__file__).resolve().parent.parent
    / "samples"
    / "sample.txt"
)


def seed_s3():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:8333",
        aws_access_key_id="localadmin",
        aws_secret_access_key="localpassword",
        region_name="us-east-1"
    )

    bucket = "document-bucket"

    buckets = s3.list_buckets()["Buckets"]

    if not any(b["Name"] == bucket for b in buckets):
        s3.create_bucket(Bucket=bucket)

    s3.upload_file(
        str(SAMPLE_PATH),
        bucket,
        "sample.txt"
    )

    print("S3 sample uploaded successfully")


def seed_azure():
    client = BlobServiceClient.from_connection_string(
        "UseDevelopmentStorage=true"
    )

    container = client.get_container_client(
        "document-container"
    )

    try:
        container.create_container()
    except ResourceExistsError:
        pass

    with SAMPLE_PATH.open("rb") as file:
        container.upload_blob(
            name="sample.txt",
            data=file,
            overwrite=True
        )

    print("Azure sample uploaded successfully")


if __name__ == "__main__":
    if not SAMPLE_PATH.is_file():
        raise FileNotFoundError(SAMPLE_PATH)

    seed_s3()
    seed_azure()

    print("Sample storage setup completed successfully")
