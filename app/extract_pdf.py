
from pathlib import Path
import json
import pymupdf


DATA_DIR = Path("data")
OUTPUT_DIR = Path("extracted")
PDF_FILES = [
    DATA_DIR / "ct200_manual.pdf",
    DATA_DIR / "ct200_manual_v2.pdf",
]


def extract_pdf(pdf_path: Path) -> dict:
    """Extract text blocks and layout metadata from one PDF."""

    pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            page_data = page.get_text("dict")
            blocks = []

            for block in page_data["blocks"]:
                # Ignore image blocks for now.
                if block.get("type") != 0:
                    continue

                lines = []
                font_sizes = []

                for line in block.get("lines", []):
                    line_text = "".join(
                        span["text"] for span in line["spans"]
                    )
                    lines.append(line_text)

                    for span in line["spans"]:
                        if span["text"].strip():
                            font_sizes.append(span["size"])

                text = "\n".join(lines).strip()

                if not text:
                    continue

                blocks.append({
                    "text": text,
                    "bbox": block["bbox"],
                    "max_font_size": max(font_sizes, default=0),
                })

            pages.append({
                "page_number": page_number,
                "blocks": blocks,
            })

    return {
        "filename": pdf_path.name,
        "page_count": len(pages),
        "pages": pages,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf_path in PDF_FILES:
        if not pdf_path.exists():
            print(f"ERROR: Missing PDF: {pdf_path}")
            continue

        result = extract_pdf(pdf_path)

        output_path = OUTPUT_DIR / f"{pdf_path.stem}.json"
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        block_count = sum(
            len(page["blocks"]) for page in result["pages"]
        )

        print(f"\nPDF: {pdf_path.name}")
        print(f"Pages: {result['page_count']}")
        print(f"Text blocks: {block_count}")
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
