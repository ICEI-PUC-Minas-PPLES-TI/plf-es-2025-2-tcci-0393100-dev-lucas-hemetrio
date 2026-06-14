from abc import ABC, abstractmethod
from typing import BinaryIO, Iterator


class StorageBackend(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Upload file bytes and return the object_name (storage path)."""

    @abstractmethod
    def upload_stream(
        self, stream: BinaryIO, object_name: str, length: int, content_type: str
    ) -> str:
        """Upload from a file-like stream without buffering it all in memory.

        Returns the object_name (storage path).
        """

    @abstractmethod
    def delete_file(self, object_name: str) -> None:
        """Delete file by its storage path/object_name."""

    @abstractmethod
    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Return a pre-signed URL for temporary read access to a file."""

    @abstractmethod
    def read_file(self, object_name: str) -> bytes:
        """Read and return the raw bytes of a stored file."""

    @abstractmethod
    def stat_file(self, object_name: str) -> int:
        """Return the size in bytes of a stored file."""

    @abstractmethod
    def stream_file(self, object_name: str, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
        """Yield the file content in chunks, without buffering it all in memory."""

    @abstractmethod
    def stream_range(
        self, object_name: str, offset: int, length: int, chunk_size: int = 1024 * 1024
    ) -> Iterator[bytes]:
        """Yield `length` bytes starting at `offset`, in chunks. For HTTP Range reads."""
