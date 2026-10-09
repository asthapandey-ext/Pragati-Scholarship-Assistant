import json, re, csv
from pathlib import Path
from search import load, search

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
answerable = [q for q in questions if q["answerable"]]

def hit(q, retrieved):
    return any(norm(a) in norm(c["text"]) for c in retrieved for a in q["answer_contains"])

rows, misses = [], []
for name in ["chunks_section.json", "chunks_fixed.json"]:
    chunks, bm25 = load(name)
    for lang in ["en", "hi"]:
        qs = [q for q in answerable if q["lang"] == lang]
        if not qs:
            continue
        h1 = h3 = 0
        for q in qs:
            res = [c for c, _ in search(q["question"], chunks, bm25, k=3)]
            ok1, ok3 = hit(q, res[:1]), hit(q, res)
            h1 += ok1
            h3 += ok3
            if not ok3:
                misses.append((name, q["id"], q["question"]))
        rows.append({"chunking": name.replace("chunks_", "").replace(".json", ""),
                     "retriever": "BM25", "language": lang, "questions": len(qs),
                     "hit@1": round(h1 / len(qs), 2), "hit@3": round(h3 / len(qs), 2)})

print(f"{'chunking':10} {'retriever':9} {'lang':5} {'n':>3} {'hit@1':>6} {'hit@3':>6}")
for r in rows:
    print(f"{r['chunking']:10} {r['retriever']:9} {r['language']:5} {r['questions']:>3} {r['hit@1']:>6} {r['hit@3']:>6}")

print("\nQuestions where the answer was NOT in the top 3:")
for name, qid, q in misses:
    print(f"  {name} | {qid} | {q}")

with open("eval/results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("\nSaved eval/results.csv")
