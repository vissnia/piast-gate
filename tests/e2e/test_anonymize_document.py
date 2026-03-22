from io import BytesIO
import docx

def create_dummy_docx():
    """Create a dummy docx file in memory."""
    doc = docx.Document()
    doc.add_paragraph("Jan Kowalski (PESEL: 90010112345) to plik testowy.")
    f = BytesIO()
    doc.save(f)
    f.seek(0)
    return f.read()

def test_anonymize_document_success(client, auth_headers):
    """Test successful anonymization of a docx document."""
    file_bytes = create_dummy_docx()
    
    files = {
        "file": ("test.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    
    response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)
    
    assert response.status_code == 200
    
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    assert "anonymized_test.docx" in response.headers["Content-Disposition"]
    
    result_stream = BytesIO(response.content)
    result_doc = docx.Document(result_stream)
    
    text = "\n".join([p.text for p in result_doc.paragraphs])
    assert "90010112345" not in text
    assert "<PERSON" in text or "<PESEL" in text
    

def test_anonymize_document_unauthorized(client):
    """Test anonymization without API key fails with 401."""
    file_bytes = b"dummy"
    files = {
        "file": ("test.txt", file_bytes, "text/plain")
    }
    response = client.post("/v1/api/anonymize", files=files)
    
    assert response.status_code == 401

def test_anonymize_document_too_large(client, auth_headers):
    """Test anonymization of an oversized file fails with 413."""
    from api.config.config import settings
    old_size = settings.max_upload_size
    settings.max_upload_size = 100
    
    try:
        file_bytes = b"A" * 101
        files = {
            "file": ("large.txt", file_bytes, "text/plain")
        }
        response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)
        
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    finally:
        settings.max_upload_size = old_size
