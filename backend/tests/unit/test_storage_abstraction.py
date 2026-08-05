"""Unit tests for MedVault Storage Abstraction Layer (Sprint 1.5)."""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from app.core.config.settings import Settings
from app.core.storage.base import StorageMetadata, StorageObject, StorageProvider
from app.core.storage.factory import get_storage_provider
from app.core.storage.local_provider import LocalStorageProvider
from app.core.storage.s3_provider import S3StorageProvider


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=str(tmp_path / "uploads"),
        storage_provider="local",
        s3_bucket="medvault-test",
        s3_endpoint="http://localhost:9000",
        s3_access_key="minioadmin",
        s3_secret_key="minioadmin",
    )


class TestLocalStorageProvider:
    def test_upload_and_download(self, mock_settings: Settings) -> None:
        provider = LocalStorageProvider(mock_settings)
        key = "test_user/test_family/doc123.pdf"
        data = b"Hello MedVault Storage Abstraction"

        obj: StorageObject = provider.upload(key, data, content_type="application/pdf")
        assert obj.object_key == key
        assert obj.size_bytes == len(data)
        assert obj.content_type == "application/pdf"
        assert len(obj.checksum) == 64  # SHA-256

        # Exists
        assert provider.exists(key) is True

        # Download
        downloaded = provider.download(key)
        assert downloaded == data

        # Stat
        meta: StorageMetadata = provider.stat(key)
        assert meta.object_key == key
        assert meta.size_bytes == len(data)

        # Download to file
        temp_dest = Path(mock_settings.upload_dir) / "temp" / "doc123.pdf"
        provider.download_file(key, temp_dest)
        assert temp_dest.is_file()
        assert temp_dest.read_bytes() == data

        # Delete
        provider.delete(key)
        assert provider.exists(key) is False

    def test_copy_and_move(self, mock_settings: Settings) -> None:
        provider = LocalStorageProvider(mock_settings)
        src_key = "docs/src.pdf"
        dst_key = "docs/dst.pdf"
        data = b"Copy & Move Test Data"

        provider.upload(src_key, data)
        assert provider.exists(src_key) is True

        # Copy
        provider.copy(src_key, dst_key)
        assert provider.exists(src_key) is True
        assert provider.exists(dst_key) is True
        assert provider.download(dst_key) == data

        # Move
        move_key = "docs/moved.pdf"
        provider.move(dst_key, move_key)
        assert provider.exists(dst_key) is False
        assert provider.exists(move_key) is True
        assert provider.download(move_key) == data


class TestStorageFactory:
    def test_factory_returns_local_provider(self, mock_settings: Settings) -> None:
        provider = get_storage_provider(mock_settings)
        assert isinstance(provider, LocalStorageProvider)

    @patch("app.core.storage.s3_provider.boto3.client")
    def test_factory_returns_s3_provider(self, mock_boto_client: MagicMock, mock_settings: Settings) -> None:
        s3_settings = Settings(
            upload_dir=mock_settings.upload_dir,
            storage_provider="minio",
            s3_bucket="medvault",
            s3_endpoint="http://localhost:9000",
        )
        provider = get_storage_provider(s3_settings)
        assert isinstance(provider, S3StorageProvider)


class TestS3StorageProvider:
    @patch("app.core.storage.s3_provider.boto3.client")
    def test_s3_upload_and_presigned_url(self, mock_boto_client: MagicMock, mock_settings: Settings) -> None:
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "https://minio.local/medvault/test.pdf?sig=123"

        s3_settings = Settings(
            upload_dir=mock_settings.upload_dir,
            storage_provider="minio",
            s3_bucket="medvault",
            s3_endpoint="http://localhost:9000",
        )
        provider = S3StorageProvider(s3_settings)

        # Upload
        data = b"S3 Object Data"
        obj = provider.upload("user1/doc.pdf", data, content_type="application/pdf")
        assert obj.object_key == "user1/doc.pdf"
        assert obj.bucket == "medvault"
        mock_s3.upload_fileobj.assert_called_once()

        # Presigned URL
        url = provider.generate_presigned_url("user1/doc.pdf", expires_in=1800)
        assert url == "https://minio.local/medvault/test.pdf?sig=123"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "medvault", "Key": "user1/doc.pdf"},
            ExpiresIn=1800,
        )
