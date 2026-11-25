
import time

from fastapi.testclient import TestClient
from app.main import app


def test_document_processing_pipeline():

    sample_text = "Cloud Document Processing Engine integration test."

    with TestClient(app) as client:

        # Step 1: Upload a sample document
        upload_response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "integration_test.txt",
                    sample_text.encode("utf-8"),
                    "text/plain"
                )
            }
        )

        assert upload_response.status_code == 200

        document_id = upload_response.json()["document_id"]

        # Step 2: Start asynchronous processing
        process_response = client.post(
            f"/documents/{document_id}/process-async"
        )

        assert process_response.status_code == 200

        task_id = process_response.json()["task_id"]

        # Step 3: Wait for Celery processing
        deadline = time.monotonic() + 60

        while time.monotonic() < deadline:

            task_response = client.get(
                f"/documents/tasks/{task_id}/status"
            )

            assert task_response.status_code == 200

            task_status = task_response.json()["status"]

            if task_status == "SUCCESS":
                break

            assert task_status not in ("FAILURE", "REVOKED"), (
                task_response.json()
            )

            time.sleep(1)

        else:
            raise AssertionError("Document processing timed out")

        # Step 4: Verify document status
        document_response = client.get(
            f"/documents/{document_id}"
        )

        assert document_response.status_code == 200
        assert document_response.json()["status"] == "completed"
        assert document_response.json()["source"] == "local_upload"

        # Step 5: Verify extracted text
        text_response = client.get(
            f"/documents/{document_id}/text"
        )

        assert text_response.status_code == 200
        assert sample_text in text_response.json()["extracted_text"]

        # Step 6: Verify extracted metadata
        metadata_response = client.get(
            f"/documents/{document_id}/metadata"
        )

        assert metadata_response.status_code == 200
        assert metadata_response.json()["metadata"]
