"""Upload-stage ingestion tests using LocalDocumentStorage + fixture PDFs."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.config.settings import Settings
from app.modules.documents.exceptions import FileTooLargeError, InvalidFileTypeError
from app.modules.documents.storage import LocalDocumentStorage
from tests.conftest import make_upload_file


@pytest.mark.asyncio
async def test_upload_saves_pdf_to_disk(
    extraction_settings: Settings,
    medical_fixture_pdfs: list[Path],
) -> None:
    storage = LocalDocumentStorage(extraction_settings)
    user_id, family_id = uuid4(), uuid4()
    source = medical_fixture_pdfs[0]
    upload = make_upload_file(source)

    try:
        saved = await storage.save(
            user_id=user_id,
            family_member_id=family_id,
            upload=upload,
        )
    finally:
        await upload.close()

    assert saved.original_filename == source.name
    assert saved.content_type == "application/pdf"
    assert saved.file_size_bytes == source.stat().st_size
    assert saved.file_size_bytes > 0

    resolved = storage.resolve_path(saved.storage_path)
    assert resolved.is_file()
    assert resolved.read_bytes() == source.read_bytes()
    assert str(user_id) in saved.storage_path
    assert str(family_id) in saved.storage_path


@pytest.mark.asyncio
async def test_upload_multiple_medical_pdfs(
    extraction_settings: Settings,
    medical_fixture_pdfs: list[Path],
) -> None:
    storage = LocalDocumentStorage(extraction_settings)
    user_id, family_id = uuid4(), uuid4()

    for source in medical_fixture_pdfs[:4]:
        upload = make_upload_file(source)
        try:
            saved = await storage.save(
                user_id=user_id,
                family_member_id=family_id,
                upload=upload,
            )
        finally:
            await upload.close()

        assert storage.resolve_path(saved.storage_path).is_file()
        assert saved.original_filename.endswith(".pdf")


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_extension(
    extraction_settings: Settings,
) -> None:
    storage = LocalDocumentStorage(extraction_settings)
    upload = UploadFile(
        file=BytesIO(b"not a pdf"),
        filename="notes.txt",
        headers=Headers({"content-type": "text/plain"}),
    )
    try:
        with pytest.raises(InvalidFileTypeError):
            await storage.save(
                user_id=uuid4(),
                family_member_id=uuid4(),
                upload=upload,
            )
    finally:
        await upload.close()


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(extraction_settings: Settings) -> None:
    storage = LocalDocumentStorage(extraction_settings)
    upload = UploadFile(
        file=BytesIO(b""),
        filename="empty.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )
    try:
        with pytest.raises(InvalidFileTypeError, match="empty"):
            await storage.save(
                user_id=uuid4(),
                family_member_id=uuid4(),
                upload=upload,
            )
    finally:
        await upload.close()


@pytest.mark.asyncio
async def test_upload_rejects_oversized_file(tmp_path: Path) -> None:
    settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        max_upload_size_mb=1,
        extraction_cache_dir=str(tmp_path / "cache"),
    )
    storage = LocalDocumentStorage(settings)
    # Just over 1 MB
    payload = b"%PDF-1.4\n" + (b"x" * (1024 * 1024))
    upload = UploadFile(
        file=BytesIO(payload),
        filename="huge.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )
    try:
        with pytest.raises(FileTooLargeError):
            await storage.save(
                user_id=uuid4(),
                family_member_id=uuid4(),
                upload=upload,
            )
    finally:
        await upload.close()


@pytest.mark.asyncio
async def test_upload_then_resolve_roundtrip(
    extraction_settings: Settings,
    dummy_dataset_dir: Path,
) -> None:
    """Upload lands on disk in the shape ExtractionEngine expects."""
    storage = LocalDocumentStorage(extraction_settings)
    source = dummy_dataset_dir / "Sophia_Patel_Blood_Report.pdf"
    upload = make_upload_file(source)
    try:
        saved = await storage.save(
            user_id=uuid4(),
            family_member_id=uuid4(),
            upload=upload,
        )
    finally:
        await upload.close()

    path = storage.resolve_path(saved.storage_path)
    assert path.suffix == ".pdf"
    assert path.stat().st_size == saved.file_size_bytes


@pytest.mark.asyncio
async def test_s3_storage_provider_unreachable(extraction_settings: Settings) -> None:
    from unittest.mock import MagicMock, patch
    from botocore.exceptions import EndpointConnectionError
    from app.core.exceptions import StorageUnavailableError
    from app.core.storage.s3_provider import S3StorageProvider

    with patch("app.core.storage.s3_provider.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        mock_s3.upload_fileobj.side_effect = EndpointConnectionError(
            endpoint_url="http://localhost:9000"
        )
        provider = S3StorageProvider(extraction_settings)
        upload = UploadFile(
            file=BytesIO(b"%PDF-1.4 sample pdf content"),
            filename="sample.pdf",
            headers=Headers({"content-type": "application/pdf"}),
        )
        storage = LocalDocumentStorage(extraction_settings, provider=provider)
        with pytest.raises(StorageUnavailableError):
            await storage.save(
                user_id=uuid4(),
                family_member_id=uuid4(),
                upload=upload,
            )

