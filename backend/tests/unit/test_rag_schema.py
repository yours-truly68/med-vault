"""Regression tests for RAG schema validation and SupportingLabValue coercion."""

from __future__ import annotations

import pytest
from app.ai.schemas.rag import GroundedAnswer, RagSupportingDetails, SupportingLabValue
from app.modules.chat.schemas import ChatSupportingDetails


def test_rag_schema_structured_lab_values():
    """Verify that structured dict objects in lab_values are correctly parsed."""
    payload = {
        "answer": "Patient's HbA1c is slightly elevated.",
        "supporting_details": {
            "patient": "John Doe",
            "lab_values": [
                {
                    "test_name": "HbA1c",
                    "value": 5.8,
                    "unit": "%",
                    "reference_high": 5.7,
                },
                {
                    "test_name": "Glucose (Fasting)",
                    "value": 108,
                    "unit": "mg/dL",
                    "reference_low": 70,
                    "reference_high": 99,
                },
            ],
        },
    }

    grounded = GroundedAnswer.model_validate(payload)
    assert grounded.supporting_details is not None
    assert len(grounded.supporting_details.lab_values) == 2

    lab1 = grounded.supporting_details.lab_values[0]
    assert isinstance(lab1, SupportingLabValue)
    assert lab1.test_name == "HbA1c"
    assert lab1.value == 5.8
    assert lab1.reference_high == 5.7

    lab2 = grounded.supporting_details.lab_values[1]
    assert lab2.test_name == "Glucose (Fasting)"
    assert lab2.value == 108


def test_rag_schema_string_lab_values():
    """Verify backward compatibility: string elements in lab_values are coerced to SupportingLabValue objects."""
    payload = {
        "answer": "Test answer",
        "supporting_details": {
            "lab_values": [
                "HbA1c: 5.8%",
                "Fasting Glucose: 108 mg/dL",
            ],
        },
    }

    grounded = GroundedAnswer.model_validate(payload)
    assert grounded.supporting_details is not None
    assert len(grounded.supporting_details.lab_values) == 2
    assert grounded.supporting_details.lab_values[0].test_name == "HbA1c: 5.8%"
    assert grounded.supporting_details.lab_values[1].test_name == "Fasting Glucose: 108 mg/dL"


def test_rag_schema_empty_lab_values():
    """Verify that empty, missing, or None lab_values validate without error."""
    payload_empty = {
        "answer": "Test answer",
        "supporting_details": {
            "lab_values": [],
        },
    }
    grounded1 = GroundedAnswer.model_validate(payload_empty)
    assert grounded1.supporting_details.lab_values == []

    payload_none = {
        "answer": "Test answer",
        "supporting_details": {
            "lab_values": None,
        },
    }
    grounded2 = GroundedAnswer.model_validate(payload_none)
    assert grounded2.supporting_details.lab_values == []


def test_rag_schema_malformed_lab_values():
    """Verify robust recovery from malformed lab_values payloads (missing test_name, numbers, nulls)."""
    payload_malformed = {
        "answer": "Test answer",
        "supporting_details": {
            "lab_values": [
                {"name": "Vitamin D", "value": 24},  # missing test_name, has 'name'
                {"value": 100},                      # missing test_name and name
                None,                                # null element
                150.5,                               # raw number
            ],
        },
    }

    grounded = GroundedAnswer.model_validate(payload_malformed)
    assert grounded.supporting_details is not None
    labs = grounded.supporting_details.lab_values
    assert len(labs) == 3  # None is filtered out

    assert labs[0].test_name == "Vitamin D"
    assert labs[0].value == 24
    assert labs[1].test_name == "Lab Result"
    assert labs[2].test_name == "Measurement: 150.5"


def test_chat_schema_supporting_details_validation():
    """Verify ChatSupportingDetails validates structured lab values for API responses."""
    details = ChatSupportingDetails.model_validate(
        {
            "patient": "Jane Doe",
            "lab_values": [
                {"test_name": "Thyroid TSH", "value": 2.5, "unit": "uIU/mL"},
            ],
        }
    )
    assert len(details.lab_values) == 1
    assert details.lab_values[0].test_name == "Thyroid TSH"
    assert details.lab_values[0].value == 2.5
