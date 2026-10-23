import json
from pathlib import Path

from app.structure_manual import build_hierarchy


def main():
    input_dir = Path("extracted")
    output_dir = Path("structured")
    output_dir.mkdir(exist_ok=True)

    for input_path in sorted(input_dir.glob("ct200_manual*.json")):
        data = json.loads(input_path.read_text(encoding="utf-8"))

        blocks = [
            {**block, "page_number": page["page_number"]}
            for page in data["pages"]
            for block in page["blocks"]
        ]

        tree = build_hierarchy(blocks)
        tree["source_filename"] = data["filename"]
        tree["page_count"] = data["page_count"]

        output_path = output_dir / f"{input_path.stem}_hierarchy.json"
        output_path.write_text(
            json.dumps(tree, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Built: {output_path}")


if __name__ == "__main__":
    main()
