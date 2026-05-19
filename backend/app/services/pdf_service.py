from pathlib import Path

import fitz  # PyMuPDF

from app.core.config import PDF_DPI


def pdf_to_images(
    pdf_path: str | Path,
    output_dir: str | Path,
    dpi: int = PDF_DPI,
    force_recreate: bool = True,
) -> list[str]:
    """
    Convert a PDF into page images.

    Input:
    - pdf_path: path to scanned PDF
    - output_dir: folder where page PNG files will be saved

    Output:
    - list of generated image paths
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(output_dir.glob(f"{pdf_path.stem}_page_*.png"))
    if existing and not force_recreate:
        return [str(p) for p in existing]

    for p in existing:
        p.unlink()

    doc = fitz.open(str(pdf_path))
    image_paths: list[str] = []

    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        out_path = output_dir / f"{pdf_path.stem}_page_{i}.png"
        pix.save(str(out_path))
        image_paths.append(str(out_path))

    doc.close()
    return image_paths


def extract_text_from_pdf_directly(pdf_path: str | Path) -> str:
    """
    Fast path for answer-key PDFs that contain selectable text.
    For scanned answer keys, this returns little/no text and OCR fallback is used.
    """
    doc = fitz.open(str(pdf_path))
    blocks: list[str] = []

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        if text.strip():
            blocks.append(f"\n[PAGE {i}]\n{text.strip()}")

    doc.close()
    return "\n".join(blocks).strip()



def convert_pdf_to_images(pdf_path: str | Path, output_dir: str | Path | None = None) -> list[str]:
    """
    Backward-compatible wrapper used by the older GradeOps pipeline.
    Converts a PDF into images using the new notebook-derived pdf_to_images().
    """
    pdf_path = Path(pdf_path)
    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_pages"
    return pdf_to_images(pdf_path, output_dir, dpi=PDF_DPI, force_recreate=True)
