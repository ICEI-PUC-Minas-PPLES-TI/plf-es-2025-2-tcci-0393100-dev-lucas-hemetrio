from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Upload file bytes and return the object_name (storage path)."""

    @abstractmethod
    def delete_file(self, object_name: str) -> None:
        """Delete file by its storage path/object_name."""

    @abstractmethod
    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Return a pre-signed URL for temporary read access to a file."""

    @abstractmethod
    def read_file(self, object_name: str) -> bytes:
        """Read and return the raw bytes of a stored file."""
