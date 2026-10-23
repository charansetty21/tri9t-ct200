
import json
from pathlib import Path


def load_manual(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_text_blocks(manual):
    blocks = []

    for page_number, page in enumerate(manual["pages"], start=1):
        for block in page["blocks"]:
            text = block.get("text", "").strip()

            if text:
                blocks.append({
                    "page": page_number,
                    "text": text
                })

    return blocks


def chunk_text(blocks, max_chars=1000):
    chunks = []
    current_text = []
    current_length = 0
    current_page = None

    for block in blocks:
        text = block["text"]

        if current_text and current_length + len(text) + 1 > max_chars:
            chunks.append({
                "page": current_page,
                "text": "\n".join(current_text)
            })
            current_text = []
            current_length = 0

        if not current_text:
            current_page = block["page"]

        current_text.append(text)
        current_length += len(text) + 1

    if current_text:
        chunks.append({
            "page": current_page,
            "text": "\n".join(current_text)
        })

    return chunks


if __name__ == "__main__":
    input_path = Path("extracted/ct200_manual.json")
    output_path = Path("extracted/ct200_chunks.json")

    manual = load_manual(input_path)
    blocks = extract_text_blocks(manual)
    chunks = chunk_text(blocks)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)

    print(f"Extracted blocks: {len(blocks)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Saved to: {output_path}")
