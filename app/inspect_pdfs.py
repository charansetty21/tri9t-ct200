
from pathlib import Path
import pymupdf

DATA_DIR = Path("data")
PDF_FILES = [
    DATA_DIR / "ct200_manual.pdf",
    DATA_DIR / "ct200_manual_v2.pdf",
]


def inspect_pdf(pdf_path: Path) -> None:
    print(f"\n{'=' * 70}")
    print(f"FILE: {pdf_path.name}")
    print("=" * 70)

    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return

    with pymupdf.open(pdf_path) as document:
        print(f"Total pages: {len(document)}")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")
            blocks = page.get_text("blocks")

            print(f"\n--- Page {page_number} ---")
            print(f"Text characters: {len(text)}")
            print(f"Text blocks: {len(blocks)}")
            print(text[:1200] if text.strip() else "[NO EXTRACTABLE TEXT]")


def main() -> None:
    for pdf_path in PDF_FILES:
        inspect_pdf(pdf_path)


if __name__ == "__main__":
    main()
