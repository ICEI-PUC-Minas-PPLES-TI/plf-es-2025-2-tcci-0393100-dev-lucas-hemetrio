"""TI-02 — Teste de integração de upload de arquivo no MinIO (Storage API).

Cenário (Tabela 9, doc): o serviço de biblioteca envia um stream de bytes do PDF
ao componente de Storage (MinIO). O serviço deve receber uma URL pública/assinada
do arquivo, e o conteúdo deve estar acessível por essa URL.

Roda contra uma instância MinIO de teste **dedicada e descartável** (ex.: container
Docker). Configure as variáveis e o teste roda; sem elas, é pulado:

    export MINIO_TEST_ENDPOINT="localhost:9000"
    export MINIO_TEST_ACCESS_KEY="minioadmin"
    export MINIO_TEST_SECRET_KEY="minioadmin"
    pytest tests/integration -v

ATENÇÃO: aponte para um MinIO descartável — o teste cria e apaga um bucket próprio.
"""
import os
import uuid

import pytest
import requests

MINIO_TEST_ENDPOINT = os.getenv("MINIO_TEST_ENDPOINT")
MINIO_TEST_ACCESS_KEY = os.getenv("MINIO_TEST_ACCESS_KEY", "minioadmin")
MINIO_TEST_SECRET_KEY = os.getenv("MINIO_TEST_SECRET_KEY", "minioadmin")

pytestmark = pytest.mark.skipif(
    not MINIO_TEST_ENDPOINT,
    reason="defina MINIO_TEST_ENDPOINT apontando para um MinIO de teste descartável",
)

SAMPLE_PDF_BYTES = b"%PDF-1.4 conteudo-de-teste"


@pytest.fixture
def storage():
    """Instancia o MinioStorageBackend apontado para o servidor de teste.

    Cria um bucket isolado (ti02-<uuid>) e o remove por completo ao final,
    mesmo em caso de falha.
    """
    from minio import Minio

    from app.storage.minio_backend import MinioStorageBackend

    bucket = f"ti02-{uuid.uuid4().hex[:8]}"

    client = Minio(
        MINIO_TEST_ENDPOINT,
        access_key=MINIO_TEST_ACCESS_KEY,
        secret_key=MINIO_TEST_SECRET_KEY,
        secure=False,
    )
    client.make_bucket(bucket)

    backend = MinioStorageBackend.__new__(MinioStorageBackend)
    backend._client = client
    backend._bucket = bucket

    try:
        yield backend
    finally:
        objects = client.list_objects(bucket, recursive=True)
        for obj in objects:
            client.remove_object(bucket, obj.object_name)
        client.remove_bucket(bucket)


def test_upload_retorna_object_name(storage):
    object_name = storage.upload_file(SAMPLE_PDF_BYTES, "doc.pdf", "application/pdf")
    assert object_name == "doc.pdf"


def test_presigned_url_e_acessivel_apos_upload(storage):
    storage.upload_file(SAMPLE_PDF_BYTES, "doc.pdf", "application/pdf")
    url = storage.get_presigned_url("doc.pdf")

    assert url.startswith("http")
    response = requests.get(url, timeout=10)
    assert response.status_code == 200
    assert response.content == SAMPLE_PDF_BYTES


def test_read_file_retorna_bytes_originais(storage):
    storage.upload_file(SAMPLE_PDF_BYTES, "doc.pdf", "application/pdf")
    result = storage.read_file("doc.pdf")
    assert result == SAMPLE_PDF_BYTES


def test_delete_remove_arquivo(storage):
    storage.upload_file(SAMPLE_PDF_BYTES, "doc.pdf", "application/pdf")
    storage.delete_file("doc.pdf")

    url = storage.get_presigned_url("doc.pdf")
    response = requests.get(url, timeout=10)
    assert response.status_code == 404
