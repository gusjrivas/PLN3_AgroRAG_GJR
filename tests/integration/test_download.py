import hashlib

import httpx
import pytest


def test_verified_download_and_idempotence(tmp_path):
    from agro_rag.infrastructure.download import download_file

    payload = b"%PDF-1.4\nsynthetic content"
    expected = hashlib.sha256(payload).hexdigest()
    calls = []

    def handler(request):
        calls.append(request.url)
        return httpx.Response(200, content=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        target = tmp_path / "doc.pdf"
        download_file("https://www.argentina.gob.ar/a.pdf", target, expected, client)
        download_file("https://www.argentina.gob.ar/a.pdf", target, expected, client)
    assert target.read_bytes() == payload
    assert len(calls) == 1


@pytest.mark.parametrize(
    "url,body,status",
    [
        ("https://evil.example/a.pdf", b"%PDF-test", 200),
        ("http://127.0.0.1/a.pdf", b"%PDF-test", 200),
        ("https://www.argentina.gob.ar/a.pdf", b"not a pdf", 200),
        ("https://www.argentina.gob.ar/a.pdf", b"%PDF-wrong-hash", 200),
        ("https://www.argentina.gob.ar/a.pdf", b"", 302),
    ],
)
def test_bad_download_does_not_publish(tmp_path, url, body, status):
    from agro_rag.infrastructure.download import download_file

    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, content=body))
    ) as client:
        with pytest.raises((ValueError, httpx.HTTPStatusError)):
            download_file(url, tmp_path / "doc.pdf", "0" * 64, client)
    assert not (tmp_path / "doc.pdf").exists()
