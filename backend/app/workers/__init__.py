from app.workers.interface import DocumentWorker

__all__ = ["DocumentWorker", "InProcessDocumentWorker"]


def __getattr__(name: str) -> type:
    if name == "InProcessDocumentWorker":
        from app.workers.in_process import InProcessDocumentWorker

        return InProcessDocumentWorker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
