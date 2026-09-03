import io
import os
import pytest
from fastapi.testclient import TestClient
import fitz
from docx import Document
from app.main import app

client = TestClient(app)


def get_auth_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def pdf_content(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def docx_content(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


@pytest.fixture
def admin_token():
    return get_auth_token("admin@example.com", "Admin123!")


@pytest.fixture
def agent_token():
    return get_auth_token("agent@example.com", "Agent123!")


def test_admin_upload_pdf(admin_token):
    file_content = pdf_content("Knowledge base support instructions")
    files = {"file": ("support_guide.pdf", io.BytesIO(file_content), "application/pdf")}
    
    response = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "support_guide.pdf"
    assert data["status"] == "processed"
    assert data["chunk_count"] == 1
    assert os.path.exists(data["file_path"])


def test_admin_upload_docx(admin_token):
    file_content = docx_content("Frequently asked questions and answers")
    files = {"file": ("faq_doc.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    response = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "docx"
    assert data["status"] == "processed"
    assert data["chunk_count"] == 1
    assert os.path.exists(data["file_path"])


def test_upload_invalid_file_extension(admin_token):
    file_content = b"malicious or unsupported script content"
    files = {"file": ("script.exe", io.BytesIO(file_content), "application/octet-stream")}
    
    response = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_empty_file(admin_token):
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    
    response = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_agent_cannot_upload(agent_token):
    file_content = pdf_content("Sample content")
    files = {"file": ("agent_doc.pdf", io.BytesIO(file_content), "application/pdf")}
    
    response = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert response.status_code == 403


def test_unauthenticated_cannot_upload():
    file_content = b"%PDF-1.4 sample content"
    files = {"file": ("unauth.pdf", io.BytesIO(file_content), "application/pdf")}
    
    response = client.post("/api/documents", files=files)
    assert response.status_code == 401


def test_list_documents(agent_token):
    response = client.get(
        "/api/documents",
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1


def test_get_document_detail_and_delete(admin_token, agent_token):
    # 1. Upload a temp document
    file_content = pdf_content("Temporary document for detail and delete test")
    files = {"file": ("temp_delete_test.pdf", io.BytesIO(file_content), "application/pdf")}
    
    upload_res = client.post(
        "/api/documents",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]
    file_path = upload_res.json()["file_path"]
    assert os.path.exists(file_path)

    # 2. Get document details as Support Agent
    detail_res = client.get(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == doc_id

    # 3. Agent cannot delete (403)
    agent_del = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert agent_del.status_code == 403

    # 4. Admin reprocesses document (200)
    reprocess_res = client.post(
        f"/api/documents/{doc_id}/reprocess",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reprocess_res.status_code == 200
    assert reprocess_res.json()["status"] == "processed"

    # 5. Admin deletes document (204)
    del_res = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 204
    assert not os.path.exists(file_path)

    # 6. Detail of deleted document should now be 404
    not_found_res = client.get(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert not_found_res.status_code == 404
