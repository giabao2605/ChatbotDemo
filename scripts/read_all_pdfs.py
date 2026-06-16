"""Script tam thoi de doc text tu tat ca PDF trong Data_Goc."""
import fitz
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_goc = os.path.join(base_dir, "Data_Goc")
output_file = os.path.join(base_dir, "scripts", "pdf_contents.txt")

with open(output_file, "w", encoding="utf-8") as out:
    for root, dirs, files in os.walk(data_goc):
        thu_muc = os.path.basename(root) if root != data_goc else "ROOT"
        for f in sorted(files):
            if not f.lower().endswith(".pdf"):
                continue
            path = os.path.join(root, f)
            try:
                doc = fitz.open(path)
                num_pages = len(doc)
                out.write(f"\n{'='*80}\n")
                out.write(f"FILE: {thu_muc}/{f} ({num_pages} trang)\n")
                out.write(f"{'='*80}\n")
                for i in range(num_pages):
                    page = doc.load_page(i)
                    txt = page.get_text("text").strip()
                    out.write(f"\n--- Trang {i+1} ---\n")
                    out.write(txt[:3000] + "\n")
                doc.close()
            except Exception as e:
                out.write(f"\nLOI doc {thu_muc}/{f}: {e}\n")

print("Done. Output written to scripts/pdf_contents.txt")
