# ADR-001: Document Extraction Engine

## Status

Accepted — 2026-08-05

## Context

MedVault previously extracted text via a monolithic `OcrService` (`app/ai/ocr.py`) that mixed PyMuPDF native text and Tesseract OCR. That coupling:

- Forced the AI pipeline to think in “OCR” terms even for searchable PDFs
- Made it hard to add Docling, vision models, or cloud document AI
- Offered no quality-gated fallback chain

## Decision

Introduce `app/extraction/` as a dedicated Extraction Engine, separate from AI understanding.

```
Upload → Inspect → Route → Strategy chain (quality-gated) → ExtractionResult
  → Classification → Metadata+Summary → Embeddings → RAG
```

AI stages consume only `text` and `page_count`. They never branch on extractor identity.

### Strategies (ordered)

| Kind | Chain |
|------|--------|
| Image | Tesseract → Gemini Vision (last resort) |
| PDF | PyMuPDF (if searchable) → Docling → Tesseract → Gemini Vision |

### Quality score

Composite `quality_score` (0–1) drives accept / warn / fallback:

- ≥ 0.9 → accept
- 0.6–0.9 → accept with warning
- < 0.6 → try next extractor

### Pipeline stage

`ProcessingStage.EXTRACT` replaces `OCR` for new writes. Reads still treat `"ocr"` as equivalent during migration.

## Consequences

- Searchable PDFs never invoke OCR
- Gemini Vision is optional and last-resort only
- Docling is optional (`DOCLING_ENABLED`) due to heavy deps
- SHA256 content cache avoids re-extracting identical files
- `app/ai/ocr.py` is removed; no duplicate extraction logic

## Alternatives considered

1. **Keep OcrService and bolt on Docling** — rejects strategy extensibility
2. **Always use Gemini Vision** — slow, expensive, unnecessary PHI egress
3. **python-magic for sniffing** — requires libmagic on Render; use `filetype` instead
