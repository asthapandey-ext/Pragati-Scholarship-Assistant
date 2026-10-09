import json, re, sys
from pathlib import Path
from rank_bm25 import BM25Okapi

STOP = set("a an the of is are in on to for and or what how many much does do can be by with as at it its per this that from".split())

def tokenize(s):
    words = re.findall(r"[a-z0-9]+", s.lower())
    return [w for w in words if w not in STOP]

def load(name):
    chunks = json.loads(Path(f"data/clean/{name}").read_text(encoding="utf-8"))
    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
    return chunks, bm25

def search(question, chunks, bm25, k=3):
    scores = bm25.get_scores(tokenize(question))
    if max(scores) <= 0:  # nothing matched at all, so return nothing instead of random chunks
        return []
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:k]
    return [(chunks[i], float(scores[i])) for i in ranked]

if __name__ == "__main__":
    questions = sys.argv[1:] or [
        "What is the family income limit?",
        "How much scholarship amount is given per year?",
        "How many scholarships are allotted to Bihar?",
        "How do I convert CGPA to percentage?",
    ]
    for name in ["chunks_section.json", "chunks_fixed.json"]:
        chunks, bm25 = load(name)
        print("=" * 70)
        print("CHUNK TYPE:", name)
        for q in questions:
            print("\nQ:", q)
            for c, s in search(q, chunks, bm25):
                print(f"  [{s:5.2f}] {c['id']} (page {c['page']}): {c['text'][:90]}...")
