from functools import lru_cache

from app.storage.base import StorageBackend


@lru_cache(maxsize=1)
def _get_storage_instance() -> StorageBackend:
    from app.core.config import settings

    if settings.STORAGE_BACKEND == "minio":
        from app.storage.minio_backend import MinioStorageBackend
        return MinioStorageBackend()

    raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")


def get_storage() -> StorageBackend:
    return _get_storage_instance()
