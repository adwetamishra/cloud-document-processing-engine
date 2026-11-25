
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_unsupported_file_upload():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.exe",
                b"test content",
                "application/octet-stream"
            )
        }
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file format"


def test_empty_file_upload():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty files are not allowed"

def test_s3_unsupported_file():
    response = client.post(
        "/s3/import",
        json={
            "bucket_name": "document-bucket",
            "file_key": "test.exe"
        }
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file format"


def test_azure_unsupported_file():
    response = client.post(
        "/azure/import",
        json={
            "container_name": "document-container",
            "blob_name": "test.exe"
        }
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file format"


def test_saas_unsupported_file():
    response = client.post(
        "/saas/import",
        json={
            "file_url": "http://127.0.0.1:8001/documents/test.exe"
        }
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file format"


def test_saas_external_url():
    response = client.post(
        "/saas/import",
        json={
            "file_url": "https://example.com/sample.pdf"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only the local SaaS API is allowed."


def test_unsafe_filename():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "CON.pdf",
                b"test content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid filename"
