
import json
from pathlib import Path

from app.structure_manual import build_hierarchy


def find_node(nodes, heading):
    """Find a node by its exact heading, including nested children."""
    for node in nodes:
        if node["heading"] == heading:
            return node

        found = find_node(node["children"], heading)
        if found:
            return found

    return None


def test_out_of_order_headings_preserve_source_order():
    blocks = [
        {"text": "3. Device Operation", "max_font_size": 16.5},
        {"text": "3.4 Auto Shutoff", "max_font_size": 12.9},
        {"text": "3.3 Result Display and Classification", "max_font_size": 12.9},
    ]

    result = build_hierarchy(blocks)
    children = result["children"][0]["children"]

    assert [node["heading"] for node in children] == [
        "3.4 Auto Shutoff",
        "3.3 Result Display and Classification",
    ]


def test_missing_intermediate_parent_is_flagged():
    blocks = [
        {"text": "2. Physical Specifications", "max_font_size": 16.5},
        {"text": "2.1 General Specifications", "max_font_size": 12.9},
        {
            "text": "2.1.1.1 Battery Life Under Typical Use",
            "max_font_size": 11.0,
        },
    ]

    result = build_hierarchy(blocks)
    section_21 = result["children"][0]["children"][0]
    battery = section_21["children"][0]

    assert battery["heading"].endswith("Battery Life Under Typical Use")
    assert battery["parent_id"] == section_21["id"]
    assert any("2.1.1" in warning for warning in battery["warnings"])


def test_duplicate_headings_have_distinct_nodes_and_parents():
    blocks = [
        {"text": "4. Alarms", "max_font_size": 16.5},
        {"text": "4.2 Error Codes", "max_font_size": 12.9},
        {"text": "7. Troubleshooting", "max_font_size": 16.5},
        {"text": "7.1 Error Codes", "max_font_size": 12.9},
    ]

    result = build_hierarchy(blocks)
    section_4, section_7 = result["children"][0], result["children"][1]
    error_codes_4 = section_4["children"][0]
    error_codes_7 = section_7["children"][0]

    assert error_codes_4["heading"].endswith("Error Codes")
    assert error_codes_7["heading"].endswith("Error Codes")
    assert error_codes_4["id"] != error_codes_7["id"]
    assert error_codes_4["parent_id"] == section_4["id"]
    assert error_codes_7["parent_id"] == section_7["id"]


def test_real_manual_preserves_irregular_headings():
    path = Path("extracted/ct200_manual.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    blocks = [
        {**block, "page_number": page["page_number"]}
        for page in data["pages"]
        for block in page["blocks"]
    ]

    result = build_hierarchy(blocks)
    sections = result["children"]

    section_3 = find_node(sections, "3 Device Operation")
    assert section_3 is not None

    section_numbers = [
        node["source_number"] for node in section_3["children"]
    ]
    assert section_numbers.index("3.4") < section_numbers.index("3.3")

    battery = find_node(
        sections,
        "2.1.1.1 Battery Life Under Typical Use",
    )
    assert battery is not None
    assert any("2.1.1" in warning for warning in battery["warnings"])
    assert battery["source_page"] == 2
    assert battery["source_bbox"] is not None
    assert battery["source_font_size"] == 11.0


def test_all_source_blocks_are_assigned_exactly_once():
    for filename in [
        "ct200_manual.json",
        "ct200_manual_v2.json",
    ]:
        source_path = Path("extracted") / filename
        data = json.loads(source_path.read_text(encoding="utf-8"))

        blocks = [
            {**block, "page_number": page["page_number"]}
            for page in data["pages"]
            for block in page["blocks"]
        ]

        result = build_hierarchy(blocks)
        expected = {
            index
            for index, block in enumerate(blocks)
            if block.get("text", "").strip()
        }

        assigned = []
        for node in walk_nodes(result):
            if "source_index" in node:
                assigned.append(node["source_index"])

            assigned.extend(
                source["source_index"]
                for source in node["body_sources"]
            )

        assert set(assigned) == expected, filename
        assert len(assigned) == len(set(assigned)), filename


def walk_nodes(node):
    yield node
    for child in node["children"]:
        yield from walk_nodes(child)


def test_rebuilding_same_hierarchy_keeps_ids_and_hashes():
    blocks = [
        {"text": "1. Device Overview", "max_font_size": 16.5},
        {"text": "Overview text.", "max_font_size": 11.0},
    ]

    first = build_hierarchy(blocks)
    second = build_hierarchy(blocks)

    assert first["id"] == second["id"]
    assert first["content_hash"] == second["content_hash"]
    assert first["children"][0]["id"] == second["children"][0]["id"]
    assert (
        first["children"][0]["content_hash"]
        == second["children"][0]["content_hash"]
    )


def test_body_change_keeps_logical_id_but_changes_hash():
    original = build_hierarchy([
        {"text": "1. Device Overview", "max_font_size": 16.5},
        {"text": "Battery life is 300 cycles.", "max_font_size": 11.0},
    ])

    revised = build_hierarchy([
        {"text": "1. Device Overview", "max_font_size": 16.5},
        {"text": "Battery life is 250 cycles.", "max_font_size": 11.0},
    ])

    original_section = original["children"][0]
    revised_section = revised["children"][0]

    assert original_section["id"] == revised_section["id"]
    assert original_section["content_hash"] != revised_section["content_hash"]


def test_duplicate_titles_under_different_numbers_have_distinct_ids():
    result = build_hierarchy([
        {"text": "4. Alarms", "max_font_size": 16.5},
        {"text": "4.2 Error Codes", "max_font_size": 12.9},
        {"text": "7. Troubleshooting", "max_font_size": 16.5},
        {"text": "7.1 Error Codes", "max_font_size": 12.9},
    ])

    section_4 = result["children"][0]["children"][0]
    section_7 = result["children"][1]["children"][0]

    assert section_4["heading"].endswith("Error Codes")
    assert section_7["heading"].endswith("Error Codes")
    assert section_4["id"] != section_7["id"]
