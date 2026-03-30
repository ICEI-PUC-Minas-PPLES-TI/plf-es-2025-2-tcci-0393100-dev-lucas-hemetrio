from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Upload file bytes and return the object_name (storage path)."""

    @abstractmethod
    def delete_file(self, object_name: str) -> None:
        """Delete file by its storage path/object_name."""
