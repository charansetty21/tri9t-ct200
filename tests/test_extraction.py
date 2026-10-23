
import json
from pathlib import Path


def test_v1_extraction_contains_pages_and_text_blocks():
    path = Path("extracted/ct200_manual.json")

    assert path.exists(), "v1 extracted JSON file is missing"

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["page_count"] == 6
    assert len(data["pages"]) == 6

    all_blocks = [
        block
        for page in data["pages"]
        for block in page["blocks"]
    ]

    assert len(all_blocks) > 0
    assert all(block["text"].strip() for block in all_blocks)


def test_extraction_preserves_specifications_table_text():
    path = Path("extracted/ct200_manual.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    all_text = "\n".join(
        block["text"]
        for page in data["pages"]
        for block in page["blocks"]
    )

    assert "Parameter\nValue" in all_text
    assert "Measurement method\nOscillometric" in all_text
    assert "Pressure range\n0–299 mmHg" in all_text
