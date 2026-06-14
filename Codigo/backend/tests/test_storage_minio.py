"""Testes unitários dos métodos de streaming do MinioStorageBackend.

O client MinIO é mockado; não toca rede. Cobre upload_stream, stat_file e
stream_file (inclusive a liberação da conexão no finally).
"""
from unittest.mock import MagicMock

from app.storage.minio_backend import MinioStorageBackend


def _backend():
    backend = MinioStorageBackend.__new__(MinioStorageBackend)
    backend._client = MagicMock()
    backend._bucket = "bucket"
    return backend


def test_upload_stream_puts_object_with_length():
    backend = _backend()
    stream = MagicMock()

    result = backend.upload_stream(stream, "a.pdf", 42, "application/pdf")

    assert result == "a.pdf"
    backend._client.put_object.assert_called_once_with(
        "bucket", "a.pdf", stream, length=42, content_type="application/pdf"
    )


def test_stat_file_returns_size():
    backend = _backend()
    backend._client.stat_object.return_value = MagicMock(size=99)

    assert backend.stat_file("a.pdf") == 99
    backend._client.stat_object.assert_called_once_with("bucket", "a.pdf")


def test_stream_file_yields_chunks_and_releases_connection():
    backend = _backend()
    response = MagicMock()
    response.stream.return_value = iter([b"ab", b"cd"])
    backend._client.get_object.return_value = response

    chunks = list(backend.stream_file("a.pdf", chunk_size=2))

    assert chunks == [b"ab", b"cd"]
    response.close.assert_called_once()
    response.release_conn.assert_called_once()


def test_stream_range_requests_offset_and_length():
    backend = _backend()
    response = MagicMock()
    response.stream.return_value = iter([b"xy"])
    backend._client.get_object.return_value = response

    chunks = list(backend.stream_range("a.pdf", 10, 2, chunk_size=2))

    assert chunks == [b"xy"]
    backend._client.get_object.assert_called_once_with(
        "bucket", "a.pdf", offset=10, length=2
    )
    response.close.assert_called_once()
    response.release_conn.assert_called_once()
