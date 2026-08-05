"""Shared fixtures for MedVault backend tests."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.config.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_DOCUMENTS_DIR = REPO_ROOT / "test-documents"
DUMMY_DATASET_DIR = TEST_DOCUMENTS_DIR / "MedVault_Dummy_Dataset"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "llm: live LLM/gateway calls (require RUN_LLM_TESTS=1 and API credentials)",
    )


@pytest.fixture(scope="session")
def test_documents_dir() -> Path:
    assert TEST_DOCUMENTS_DIR.is_dir(), f"Missing fixtures: {TEST_DOCUMENTS_DIR}"
    return TEST_DOCUMENTS_DIR


@pytest.fixture(scope="session")
def dummy_dataset_dir(test_documents_dir: Path) -> Path:
    path = test_documents_dir / "MedVault_Dummy_Dataset"
    assert path.is_dir(), f"Missing dataset: {path}"
    return path


@pytest.fixture(scope="session")
def medical_fixture_pdfs(test_documents_dir: Path, dummy_dataset_dir: Path) -> list[Path]:
    """Representative medical PDFs from both fixture roots."""
    selected = [
        test_documents_dir / "John_Doe_Blood_Report_1.pdf",
        test_documents_dir / "Jenny_Doe_Diabetes_Report_1.pdf",
        test_documents_dir / "Joe_Doe_Oncology_Report_1.pdf",
        test_documents_dir / "John_Doe_XRay_Fracture_Report.pdf",
        dummy_dataset_dir / "John_Carter_Prescription.pdf",
        dummy_dataset_dir / "Sophia_Patel_Blood_Report.pdf",
        dummy_dataset_dir / "Emily_Carter_Hospital_Bill.pdf",
        dummy_dataset_dir / "Daniel_Kim_Diagnosis_Report.pdf",
        dummy_dataset_dir / "Michael_Brown_Scanning_Report.pdf",
    ]
    missing = [path for path in selected if not path.is_file()]
    assert not missing, f"Missing fixture PDFs: {missing}"
    return selected


@pytest.fixture(scope="session")
def non_medical_fixture_pdfs(dummy_dataset_dir: Path) -> list[Path]:
    selected = [
        dummy_dataset_dir / "Bank_Statement.pdf",
        dummy_dataset_dir / "Electricity_Bill.pdf",
        dummy_dataset_dir / "Rental_Agreement.pdf",
        dummy_dataset_dir / "Vehicle_Insurance.pdf",
        dummy_dataset_dir / "Internet_Invoice.pdf",
    ]
    missing = [path for path in selected if not path.is_file()]
    assert not missing, f"Missing non-medical fixtures: {missing}"
    return selected


@pytest.fixture(scope="session")
def all_dummy_dataset_pdfs(dummy_dataset_dir: Path) -> list[Path]:
    files = sorted(dummy_dataset_dir.glob("*.pdf"))
    assert len(files) >= 20, f"Expected a full dummy dataset, found {len(files)}"
    return files


@pytest.fixture
def extraction_settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=str(tmp_path / "uploads"),
        extraction_cache_dir=str(tmp_path / "extraction-cache"),
        extraction_cache_enabled=True,
        docling_enabled=False,
        gemini_vision_enabled=False,
        extraction_quality_accept_threshold=0.9,
        extraction_quality_warn_threshold=0.6,
        extraction_allow_low_quality_last_resort=False,
        max_upload_size_mb=25,
    )


@pytest.fixture(scope="session")
def llm_settings() -> Settings:
    """Load real env credentials for live LLM tests."""
    settings = Settings()
    key = (settings.llm_api_key or settings.openai_api_key or "").strip()
    if os.getenv("RUN_LLM_TESTS") != "1":
        pytest.skip("Set RUN_LLM_TESTS=1 to enable live LLM tests")
    if not key:
        pytest.skip("No LLM API key configured (OPENAI_API_KEY / LLM_API_KEY)")
    return settings


def make_upload_file(path: Path, *, content_type: str = "application/pdf") -> UploadFile:
    """Build a FastAPI UploadFile from a fixture path."""
    handle = path.open("rb")
    return UploadFile(
        file=handle,
        filename=path.name,
        headers=Headers({"content-type": content_type}),
    )


def new_ids() -> tuple:
    return uuid4(), uuid4()
