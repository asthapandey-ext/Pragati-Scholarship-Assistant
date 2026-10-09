import re, json
from pathlib import Path

SOURCE = "pragati_degree_2020-21"
text = Path(f"data/clean/{SOURCE}.txt").read_text(encoding="utf-8")

# remember where each page starts, so every chunk can carry a page number
marks = [(m.start(), int(m.group(1))) for m in re.finditer(r"\[PAGE (\d+)\]", text)]

def page_at(pos):
    page = 1
    for start, num in marks:
        if start <= pos:
            page = num
    return page

def tidy(s):
    s = re.sub(r"\[PAGE \d+\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# Strategy A: one chunk per numbered section + Annexure A
heading = re.compile(r"^[ \t]*(?:\d{1,2}\.0[ \t]+[A-Z][^\n]*|Annexure A)[ \t]*$", re.MULTILINE)
starts = [m.start() for m in heading.finditer(text)]
section_chunks = []
for i, s in enumerate(starts):
    e = starts[i + 1] if i + 1 < len(starts) else len(text)
    section_chunks.append({
        "id": f"{SOURCE}_sec_{i+1}",
        "source": SOURCE,
        "page": page_at(s),
        "text": tidy(text[s:e]),
    })

# Strategy B: fixed-size chunks with overlap
tokens = []
for m in re.finditer(r"\S+", text):
    w = m.group()
    if w == "[PAGE" or re.fullmatch(r"\d+\]", w):
        continue
    tokens.append((w, page_at(m.start())))

SIZE, OVERLAP = 120, 30
fixed_chunks = []
for i, start in enumerate(range(0, len(tokens), SIZE - OVERLAP)):
    piece = tokens[start:start + SIZE]
    fixed_chunks.append({
        "id": f"{SOURCE}_fix_{i+1}",
        "source": SOURCE,
        "page": piece[0][1],
        "text": " ".join(w for w, _ in piece),
    })

Path("data/clean/chunks_section.json").write_text(
    json.dumps(section_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
Path("data/clean/chunks_fixed.json").write_text(
    json.dumps(fixed_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

print("Section chunks:", len(section_chunks))
print("Fixed chunks:", len(fixed_chunks))
