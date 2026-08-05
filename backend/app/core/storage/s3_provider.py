"""S3-compatible storage provider implementation using boto3.

Supports MinIO, AWS S3, Cloudflare R2, DigitalOcean Spaces, and Backblaze B2
without requiring provider-specific application logic.
"""

from __future__ import annotations

import hashlib
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config.settings import Settings
from app.core.storage.base import StorageMetadata, StorageObject, StorageProvider

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    """Universal S3-compatible storage provider (MinIO, AWS S3, Cloudflare R2, B2, Spaces)."""

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._region = settings.s3_region
        self._endpoint = settings.s3_endpoint
        self._public_endpoint = settings.s3_public_endpoint or settings.s3_endpoint
        self._access_key = settings.s3_access_key
        self._secret_key = settings.s3_secret_key
        self._use_ssl = settings.s3_use_ssl
        self._force_path_style = settings.s3_force_path_style

        # Internal boto3 client for backend operations
        self._s3_client = boto3.client(
            "s3",
            endpoint_url=self._endpoint if self._endpoint else None,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
            use_ssl=self._use_ssl,
            config=Config(
                s3={"addressing_style": "path" if self._force_path_style else "auto"},
                signature_version="s3v4",
            ),
        )

        # Public boto3 client for presigned URLs (if public endpoint differs, e.g. localhost vs minio:9000)
        if self._public_endpoint and self._public_endpoint != self._endpoint:
            self._presign_client = boto3.client(
                "s3",
                endpoint_url=self._public_endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
                use_ssl=self._use_ssl,
                config=Config(
                    s3={"addressing_style": "path" if self._force_path_style else "auto"},
                    signature_version="s3v4",
                ),
            )
        else:
            self._presign_client = self._s3_client

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it does not already exist (useful for MinIO local dev)."""
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._s3_client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    logger.info("Bucket %s does not exist; creating...", self._bucket)
                    if self._region and self._region != "us-east-1":
                        self._s3_client.create_bucket(
                            Bucket=self._bucket,
                            CreateBucketConfiguration={"LocationConstraint": self._region},
                        )
                    else:
                        self._s3_client.create_bucket(Bucket=self._bucket)
                except Exception as create_exc:
                    logger.warning("Could not auto-create bucket %s: %s", self._bucket, create_exc)
            else:
                logger.warning("head_bucket for %s returned client error: %s", self._bucket, exc)
        except BotoCoreError as exc:
            logger.warning("S3 endpoint connection warning for %s (%s): %s", self._bucket, self._endpoint, exc)
        except Exception as exc:
            logger.warning("Unexpected error checking S3 bucket %s: %s", self._bucket, exc)

    def upload(
        self,
        object_key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StorageObject:
        if isinstance(data, bytes):
            stream = io.BytesIO(data)
        else:
            stream = data

        # Calculate SHA-256 checksum while reading
        hasher = hashlib.sha256()
        buffer = stream.read()
        hasher.update(buffer)
        checksum = hasher.hexdigest()
        size_bytes = len(buffer)

        # Reset stream position for boto3 upload
        stream_to_upload = io.BytesIO(buffer)

        extra_args: dict[str, str | dict[str, str]] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        meta = metadata or {}
        meta["sha256"] = checksum
        extra_args["Metadata"] = meta

        self._s3_client.upload_fileobj(
            stream_to_upload,
            self._bucket,
            object_key,
            ExtraArgs=extra_args if extra_args else None,
        )

        return StorageObject(
            object_key=object_key,
            bucket=self._bucket,
            size_bytes=size_bytes,
            content_type=content_type or "application/octet-stream",
            checksum=checksum,
            uploaded_at=datetime.now(timezone.utc),
        )

    def download(self, object_key: str) -> bytes:
        buffer = io.BytesIO()
        try:
            self._s3_client.download_fileobj(self._bucket, object_key, buffer)
            return buffer.getvalue()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "404":
                raise FileNotFoundError(f"Object key not found in storage: {object_key}") from exc
            raise

    def download_file(self, object_key: str, destination_path: Path) -> Path:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._s3_client.download_file(self._bucket, object_key, str(destination_path))
            return destination_path
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "404":
                raise FileNotFoundError(f"Object key not found in storage: {object_key}") from exc
            raise

    def delete(self, object_key: str) -> None:
        try:
            self._s3_client.delete_object(Bucket=self._bucket, Key=object_key)
        except ClientError as exc:
            logger.warning("Failed to delete object key %s: %s", object_key, exc)

    def exists(self, object_key: str) -> bool:
        try:
            self._s3_client.head_object(Bucket=self._bucket, Key=object_key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def stat(self, object_key: str) -> StorageMetadata:
        try:
            resp = self._s3_client.head_object(Bucket=self._bucket, Key=object_key)
            size_bytes = resp.get("ContentLength", 0)
            content_type = resp.get("ContentType", "application/octet-stream")
            etag = resp.get("ETag", "").strip('"')
            metadata = resp.get("Metadata", {})
            checksum = metadata.get("sha256")
            last_modified = resp.get("LastModified")

            return StorageMetadata(
                object_key=object_key,
                bucket=self._bucket,
                size_bytes=size_bytes,
                content_type=content_type,
                checksum=checksum,
                etag=etag,
                last_modified=last_modified,
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"Object key not found: {object_key}") from exc
            raise

    def generate_presigned_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        params: dict[str, str] = {
            "Bucket": self._bucket,
            "Key": object_key,
        }
        if filename:
            params["ResponseContentDisposition"] = f'inline; filename="{filename}"'

        return self._presign_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def copy(self, source_key: str, destination_key: str) -> None:
        copy_source = {"Bucket": self._bucket, "Key": source_key}
        self._s3_client.copy(copy_source, self._bucket, destination_key)

    def move(self, source_key: str, destination_key: str) -> None:
        self.copy(source_key, destination_key)
        self.delete(source_key)
