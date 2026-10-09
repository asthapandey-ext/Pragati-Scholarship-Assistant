import fitz  # PyMuPDF
from pathlib import Path

pdf_path = Path("data/raw/pragati_degree_2020-21.pdf")
out_path = Path("data/clean/pragati_degree_2020-21.txt")

if not pdf_path.exists():
    print(f"File not found: {pdf_path.resolve()}")
    print("Check that the PDF is in data/raw and the name matches exactly.")
    raise SystemExit(1)

out_path.parent.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf_path)
pages = []
for i, page in enumerate(doc, start=1):
    text = page.get_text()
    pages.append(f"[PAGE {i}]\n{text}")

out_path.write_text("\n".join(pages), encoding="utf-8")
print(f"Done. {len(doc)} pages saved to {out_path}")
