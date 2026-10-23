import re
from uuid import NAMESPACE_URL, uuid5


HEADING_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)*\.?)\s+(.+?)\s*$"
)


def build_hierarchy(blocks: list[dict]) -> dict:
    """Build a source-ordered hierarchy with deterministic logical IDs."""

    root = {
        "id": str(uuid5(NAMESPACE_URL, "tri9t-ct200:document")),
        "heading": "Document",
        "level": 0,
        "body": "",
        "body_sources": [],
        "parent_id": None,
        "children": [],
        "warnings": [],
    }

    stack = [root]

    for source_index, block in enumerate(blocks):
        text = block.get("text", "").strip()
        if not text:
            continue

        match = HEADING_PATTERN.match(text)
        number = match.group(1).rstrip(".") if match else None
        title = match.group(2).strip() if match else None
        level = number.count(".") + 1 if number else 0
        font_size = block.get("max_font_size") or 0

        is_heading = bool(match) and (
            (level == 1 and font_size >= 14.0)
            or level >= 2
        )

        provenance = {
            "source_index": source_index,
            "source_page": block.get("page_number"),
            "source_bbox": block.get("bbox"),
            "text": text,
        }

        if not is_heading:
            current = stack[-1]
            current["body"] += (
                ("\n" if current["body"] else "") + text
            )
            current["body_sources"].append(provenance)
            continue

        # Logical identity is independent of body text and source position.
        logical_key = f"tri9t-ct200:section:{number}"
        node = {
            "id": str(uuid5(NAMESPACE_URL, logical_key)),
            "heading": f"{number} {title}",
            "level": level,
            "body": "",
            "body_sources": [],
            "parent_id": None,
            "children": [],
            "warnings": [],
            "source_number": number,
            "source_index": source_index,
            "source_page": block.get("page_number"),
            "source_bbox": block.get("bbox"),
            "source_font_size": font_size,
        }

        while len(stack) > 1 and stack[-1]["level"] >= level:
            stack.pop()

        parent = stack[-1]

        expected_parent = (
            ".".join(number.split(".")[:-1])
            if "." in number
            else None
        )

        if expected_parent and parent.get("source_number") != expected_parent:
            node["warnings"].append(
                f"Missing intermediate parent: {expected_parent}"
            )

        node["parent_id"] = parent["id"]
        parent["children"].append(node)
        stack.append(node)

    add_content_hashes(root)
    return root


def add_content_hashes(node: dict) -> None:
    """Calculate a SHA-256 hash for each node's own heading and body."""
    import hashlib

    content = f"{node.get('heading', '')}\n{node.get('body', '')}"
    node["content_hash"] = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    for child in node["children"]:
        add_content_hashes(child)
