import json, re, csv
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from search import load, tokenize, search as bm25_search

MODEL_NAME = "intfloat/multilingual-e5-small"   # supports Hindi + English
K = 3

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

print("Loading model (first run downloads about 470 MB, please wait)...")
model = SentenceTransformer(MODEL_NAME)

def chunk_embeddings(name, chunks):
    cache = Path(f"data/clean/emb_{name.replace('.json', '')}.npy")
    if cache.exists():
        return np.load(cache)
    texts = ["passage: " + c["text"] for c in chunks]      # e5 needs this prefix
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    np.save(cache, emb)
    return emb

def dense_search(question, chunks, emb, k=K):
    q = model.encode(["query: " + question], normalize_embeddings=True)[0]   # e5 query prefix
    scores = emb @ q
    order = np.argsort(-scores)[:k]
    return [chunks[i] for i in order]

def hybrid_search(question, chunks, bm25, emb, k=K):
    # Reciprocal Rank Fusion: combine the keyword ranking and the embedding ranking
    q = model.encode(["query: " + question], normalize_embeddings=True)[0]
    dense_rank = list(np.argsort(-(emb @ q)))
    fused = {}
    for rank, i in enumerate(dense_rank):
        fused[i] = fused.get(i, 0) + 1 / (60 + rank)
    scores = bm25.get_scores(tokenize(question))
    if max(scores) > 0:
        for rank, i in enumerate(np.argsort(-scores)):
            fused[i] = fused.get(i, 0) + 1 / (60 + rank)
    order = sorted(fused, key=fused.get, reverse=True)[:k]
    return [chunks[i] for i in order]

questions = [q for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8")) if q["answerable"]]

def hit(q, retrieved):
    return any(norm(a) in norm(c["text"]) for c in retrieved for a in q["answer_contains"])

rows, misses = [], []
for name in ["chunks_section.json", "chunks_fixed.json"]:
    chunks, bm25 = load(name)
    emb = chunk_embeddings(name, chunks)
    methods = {
        "BM25":   lambda q: [c for c, _ in bm25_search(q, chunks, bm25, K)],
        "Dense":  lambda q: dense_search(q, chunks, emb),
        "Hybrid": lambda q: hybrid_search(q, chunks, bm25, emb),
    }
    for mname, fn in methods.items():
        for lang in ["en", "hi"]:
            qs = [q for q in questions if q["lang"] == lang]
            if not qs:
                continue
            h1 = h3 = 0
            for q in qs:
                res = fn(q["question"])
                h1 += hit(q, res[:1])
                ok3 = hit(q, res)
                h3 += ok3
                if not ok3:
                    misses.append((name, mname, q["id"], q["question"]))
            rows.append({"chunking": name.replace("chunks_", "").replace(".json", ""),
                         "retriever": mname, "language": lang, "questions": len(qs),
                         "hit@1": round(h1 / len(qs), 2), "hit@3": round(h3 / len(qs), 2)})

print(f"\n{'chunking':9} {'retriever':9} {'lang':5} {'n':>3} {'hit@1':>6} {'hit@3':>6}")
for r in rows:
    print(f"{r['chunking']:9} {r['retriever']:9} {r['language']:5} {r['questions']:>3} {r['hit@1']:>6} {r['hit@3']:>6}")

print("\nMisses (answer not in top 3):")
for name, m, qid, q in misses:
    print(f"  {name.replace('chunks_','').replace('.json','')} | {m} | {qid} | {q}")

with open("eval/results_all.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("\nSaved eval/results_all.csv")
