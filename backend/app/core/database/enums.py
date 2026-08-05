from enum import StrEnum

# Default dimension for OpenAI text-embedding-3-small (and compatible models).
EMBEDDING_DIMENSIONS = 1536


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    INDEXING = "indexing"
    INDEXED = "indexed"
    COMPLETED = "completed"  # Alias for READY / INDEXED backward compatibility
    FAILED = "failed"
    REJECTED = "rejected"


class IndexingStatus(StrEnum):
    NOT_STARTED = "not_started"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentType(StrEnum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    HOSPITAL_BILL = "hospital_bill"
    PHARMACY_BILL = "pharmacy_bill"
    DISCHARGE_SUMMARY = "discharge_summary"
    IMAGING_REPORT = "imaging_report"
    OTHER = "other"
    UNRELATED = "unrelated"


class TimelineEventType(StrEnum):
    DOCUMENT = "document"
    ADMISSION = "admission"
    DISCHARGE = "discharge"
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    LAB_RESULT = "lab_result"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    DEVICE = "device"
    VACCINATION = "vaccination"
    FOLLOW_UP = "follow_up"
    VISIT = "visit"
    IMAGING = "imaging"


class ProcessingStage(StrEnum):
    UPLOADED = "uploaded"
    EXTRACT = "extract"
    OCR = "ocr"  # Deprecated alias of EXTRACT — dual-read during migration
    CLASSIFICATION = "classification"
    METADATA = "metadata"
    SUMMARY = "summary"
    METADATA_SUMMARY = "metadata_summary"
    EMBEDDINGS = "embeddings"
    READY = "ready"
    FAILED = "failed"


def is_extraction_stage(stage: ProcessingStage | str) -> bool:
    value = stage.value if isinstance(stage, ProcessingStage) else stage
    return value in {ProcessingStage.EXTRACT.value, ProcessingStage.OCR.value}


class ProcessingJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    RATE_LIMITED = "rate_limited"
    COMPLETED = "completed"
    FAILED = "failed"
