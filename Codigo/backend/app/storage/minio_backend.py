import io

from minio import Minio

from app.core.config import settings
from app.storage.base import StorageBackend


class MinioStorageBackend(StorageBackend):
    def __init__(self):
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self._bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )
        return object_name

    def delete_file(self, object_name: str) -> None:
        self._client.remove_object(self._bucket, object_name)
