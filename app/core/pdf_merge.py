from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader, PdfWriter


def merge_pdfs(pdf_paths, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()

    for pdf in pdf_paths:
        reader = PdfReader(str(pdf))
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
