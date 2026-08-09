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

def create_dummy_pdf():
    """Build a minimal single-page PDF (no external PDF library needed) containing PII text."""
    text = "Jan Kowalski PESEL 90010112345"
    content = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, obj)

    xref_offset = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off

    out += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF" % xref_offset
    return bytes(out)

def test_anonymize_document_success(client, auth_headers):
    """Test successful anonymization of a docx document."""
    file_bytes = create_dummy_docx()

    files = {
        "file": ("test.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

    response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)

    assert response.status_code == 200

    body = response.json()
    text = body["anonymized_text"]
    assert "90010112345" not in text
    assert "<PERSON" in text or "<PESEL" in text


def test_anonymize_pdf_document_success(client, auth_headers):
    """Test successful anonymization of a pdf document."""
    file_bytes = create_dummy_pdf()

    files = {
        "file": ("test.pdf", file_bytes, "application/pdf")
    }

    response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)

    assert response.status_code == 200

    body = response.json()
    text = body["anonymized_text"]
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
