from pathlib import Path
import json


def flatten_tree(root: dict) -> dict:
    """Return all hierarchy nodes keyed by their logical ID."""
    nodes = {}

    def visit(node):
        if node["level"] > 0:
            nodes[node["id"]] = node

        for child in node["children"]:
            visit(child)

    visit(root)
    return nodes


def compare_versions(old_tree: dict, new_tree: dict) -> dict:
    """Compare two hierarchy trees using logical IDs and content hashes."""
    old_nodes = flatten_tree(old_tree)
    new_nodes = flatten_tree(new_tree)

    old_ids = set(old_nodes)
    new_ids = set(new_nodes)

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    changed = []
    unchanged = []

    for node_id in sorted(old_ids & new_ids):
        old_node = old_nodes[node_id]
        new_node = new_nodes[node_id]

        if old_node["content_hash"] != new_node["content_hash"]:
            changed.append({
                "id": node_id,
                "old_heading": old_node["heading"],
                "new_heading": new_node["heading"],
                "old_hash": old_node["content_hash"],
                "new_hash": new_node["content_hash"],
            })
        else:
            unchanged.append(node_id)

    return {
        "added": [
            {"id": node_id, "heading": new_nodes[node_id]["heading"]}
            for node_id in added
        ],
        "removed": [
            {"id": node_id, "heading": old_nodes[node_id]["heading"]}
            for node_id in removed
        ],
        "changed": changed,
        "unchanged": unchanged,
    }


def main():
    old_path = Path("structured/ct200_manual_hierarchy.json")
    new_path = Path("structured/ct200_manual_v2_hierarchy.json")

    old_tree = json.loads(old_path.read_text(encoding="utf-8"))
    new_tree = json.loads(new_path.read_text(encoding="utf-8"))

    result = compare_versions(old_tree, new_tree)

    output_path = Path("structured/version_diff.json")
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Added sections:", len(result["added"]))
    print("Removed sections:", len(result["removed"]))
    print("Changed sections:", len(result["changed"]))
    print("Unchanged sections:", len(result["unchanged"]))
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
