"""Extraction quality scoring and accept/warn/reject decisions."""

from __future__ import annotations

import re
from collections import Counter

from app.extraction.models import (
    QualityComponents,
    QualityDecision,
    QualityScore,
    RawExtraction,
)

MEDICAL_KEYWORDS = frozenset({
    "patient",
    "diagnosis",
    "prescription",
    "dosage",
    "hospital",
    "doctor",
    "physician",
    "clinic",
    "lab",
    "laboratory",
    "hemoglobin",
    "creatinine",
    "glucose",
    "cholesterol",
    "discharge",
    "admission",
    "imaging",
    "radiology",
    "x-ray",
    "mri",
    "ct",
    "ultrasound",
    "medication",
    "medicine",
    "tablet",
    "capsule",
    "mg",
    "ml",
    "rx",
    "allergy",
    "blood",
    "urine",
    "report",
    "result",
    "findings",
    "treatment",
    "follow-up",
    "followup",
})

_WORD_RE = re.compile(r"[A-Za-z]{3,}")
_VOWELS = set("aeiouAEIOU")


class QualityScorer:
    def __init__(
        self,
        *,
        accept_threshold: float = 0.9,
        warn_threshold: float = 0.6,
        w_printable: float = 0.25,
        w_ocr_confidence: float = 0.25,
        w_density: float = 0.20,
        w_medical: float = 0.15,
        w_garbled: float = 0.15,
    ) -> None:
        self._accept = accept_threshold
        self._warn = warn_threshold
        self._w_printable = w_printable
        self._w_ocr = w_ocr_confidence
        self._w_density = w_density
        self._w_medical = w_medical
        self._w_garbled = w_garbled

    def score(
        self,
        raw: RawExtraction,
        *,
        is_ocr: bool = False,
    ) -> QualityScore:
        text = raw.text or ""
        stripped = text.strip()
        reasons: list[str] = []

        if not stripped:
            components = QualityComponents(
                printable_ratio=0.0,
                ocr_confidence=0.0,
                text_density=0.0,
                medical_keyword_score=0.0,
                garbled_penalty=0.0,
            )
            return QualityScore(
                score=0.0,
                decision=QualityDecision.REJECT,
                components=components,
                reasons=["empty_text"],
            )

        printable = self._printable_ratio(stripped)
        ocr_conf = self._ocr_confidence(raw, is_ocr=is_ocr)
        density = self._text_density(stripped, raw.page_count)
        medical = self._medical_keyword_score(stripped)
        garbled = self._garbled_penalty(stripped)

        score = (
            self._w_printable * printable
            + self._w_ocr * ocr_conf
            + self._w_density * density
            + self._w_medical * medical
            + self._w_garbled * garbled
        )
        score = max(0.0, min(1.0, score))

        if printable < 0.7:
            reasons.append("low_printable_ratio")
        if density < 0.3:
            reasons.append("low_text_density")
        if garbled < 0.5:
            reasons.append("garbled_output")
        if medical < 0.2:
            reasons.append("few_medical_keywords")
        if is_ocr and ocr_conf < 0.5:
            reasons.append("low_ocr_confidence")

        if score >= self._accept:
            decision = QualityDecision.ACCEPT
        elif score >= self._warn:
            decision = QualityDecision.ACCEPT_WITH_WARN
            if not reasons:
                reasons.append("borderline_quality")
        else:
            decision = QualityDecision.REJECT
            if not reasons:
                reasons.append("below_quality_threshold")

        return QualityScore(
            score=score,
            decision=decision,
            components=QualityComponents(
                printable_ratio=printable,
                ocr_confidence=ocr_conf,
                text_density=density,
                medical_keyword_score=medical,
                garbled_penalty=garbled,
            ),
            reasons=reasons,
        )

    def _printable_ratio(self, text: str) -> float:
        if not text:
            return 0.0
        printable = 0
        for ch in text:
            code = ord(ch)
            if ch.isspace() or 0x20 <= code <= 0x7E or code > 0xA0:
                printable += 1
        return printable / len(text)

    def _ocr_confidence(self, raw: RawExtraction, *, is_ocr: bool) -> float:
        if raw.extractor_confidence is not None:
            return max(0.0, min(1.0, raw.extractor_confidence))
        if not is_ocr:
            return 1.0
        return 0.5

    def _text_density(self, text: str, page_count: int) -> float:
        pages = max(page_count, 1)
        chars_per_page = len(text.strip()) / pages
        if chars_per_page < 50:
            return max(0.0, chars_per_page / 50 * 0.2)
        if chars_per_page < 200:
            return 0.2 + (chars_per_page - 50) / 150 * 0.3
        if chars_per_page <= 2500:
            return 0.5 + (chars_per_page - 200) / 2300 * 0.5
        if chars_per_page <= 6000:
            return 1.0 - (chars_per_page - 2500) / 3500 * 0.15
        return max(0.4, 0.85 - (chars_per_page - 6000) / 10000)

    def _medical_keyword_score(self, text: str) -> float:
        lower = text.lower()
        hits = {kw for kw in MEDICAL_KEYWORDS if kw in lower}
        return min(1.0, len(hits) / 5.0)

    def _garbled_penalty(self, text: str) -> float:
        """Return 1.0 for clean text, lower when garbled."""
        words = _WORD_RE.findall(text)
        if not words:
            symbol_ratio = sum(1 for ch in text if not ch.isalnum() and not ch.isspace()) / max(
                len(text), 1
            )
            return max(0.0, 1.0 - symbol_ratio * 2)

        low_vowel = 0
        for word in words[:500]:
            vowels = sum(1 for ch in word if ch in _VOWELS)
            if len(word) >= 5 and vowels / len(word) < 0.15:
                low_vowel += 1
        vowel_signal = low_vowel / max(len(words[:500]), 1)

        replacement = text.count("\ufffd") / max(len(text), 1)
        symbol_ratio = sum(1 for ch in text if not ch.isalnum() and not ch.isspace()) / max(
            len(text), 1
        )

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        repeat_signal = 0.0
        if len(lines) >= 4:
            counts = Counter(lines)
            most_common = counts.most_common(1)[0][1]
            repeat_signal = max(0.0, (most_common / len(lines)) - 0.3)

        garbled = min(
            1.0,
            vowel_signal * 1.5 + replacement * 8 + max(0.0, symbol_ratio - 0.25) + repeat_signal,
        )
        return max(0.0, 1.0 - garbled)
