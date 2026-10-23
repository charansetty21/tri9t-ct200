from app.compare_versions import compare_versions


def make_node(node_id, heading, content_hash, children=None):
    return {
        "id": node_id,
        "heading": heading,
        "level": 1,
        "content_hash": content_hash,
        "children": children or [],
    }


def make_tree(*nodes):
    return {
        "id": "root",
        "heading": "Document",
        "level": 0,
        "children": list(nodes),
    }


def test_version_diff_detects_added_removed_changed_and_unchanged():
    old_tree = make_tree(
        make_node("section-1", "1 Introduction", "hash-a"),
        make_node("section-2", "2 Specifications", "hash-b"),
        make_node("section-3", "3 Operation", "hash-c"),
    )

    new_tree = make_tree(
        make_node("section-1", "1 Introduction", "hash-a"),
        make_node("section-2", "2 Specifications", "hash-b-updated"),
        make_node("section-4", "4 Data Export", "hash-d"),
    )

    result = compare_versions(old_tree, new_tree)

    assert [item["heading"] for item in result["added"]] == [
        "4 Data Export"
    ]
    assert [item["heading"] for item in result["removed"]] == [
        "3 Operation"
    ]
    assert len(result["changed"]) == 1
    assert result["changed"][0]["id"] == "section-2"
    assert result["unchanged"] == ["section-1"]


def test_real_manual_versions_detect_expected_changes():
    import json
    from pathlib import Path

    old_tree = json.loads(
        Path("structured/ct200_manual_hierarchy.json").read_text(
            encoding="utf-8"
        )
    )
    new_tree = json.loads(
        Path("structured/ct200_manual_v2_hierarchy.json").read_text(
            encoding="utf-8"
        )
    )

    result = compare_versions(old_tree, new_tree)

    added_headings = {item["heading"] for item in result["added"]}
    changed_headings = {
        item["old_heading"] for item in result["changed"]
    }

    assert "5.3 Data Export" in added_headings
    assert "2.1.1.1 Battery Life Under Typical Use" in changed_headings
    assert "3.2 Cuﬀ Inﬂation Sequence" in changed_headings
    assert "4 Alarms and Safety Behavior" not in changed_headings
    assert result["removed"] == []
