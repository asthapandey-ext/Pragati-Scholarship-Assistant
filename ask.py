import sys, json, re
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from search import load, tokenize

MODEL_NAME = "intfloat/multilingual-e5-small"
CHUNKS_FILE = "chunks_section.json"          # best setup from your evaluation
DOC_NOTE = "Source document: AICTE Pragati (Degree) guidelines 2020-21 (July 2020). Rules may have changed, so check the official portal."
THRESHOLD_FILE = Path("eval/threshold.json")

print("Loading model...")
model = SentenceTransformer(MODEL_NAME)
chunks, bm25 = load(CHUNKS_FILE)

cache = Path("data/clean/emb_chunks_section.npy")
if cache.exists():
    emb = np.load(cache)
else:
    emb = model.encode(["passage: " + c["text"] for c in chunks], normalize_embeddings=True)
    np.save(cache, emb)

def retrieve(question, k=3):
    """Hybrid search (embeddings + keywords). Also returns the best embedding similarity."""
    q = model.encode(["query: " + question], normalize_embeddings=True)[0]
    dense = emb @ q
    fused = {}
    for rank, i in enumerate(np.argsort(-dense)):
        fused[i] = fused.get(i, 0) + 1 / (60 + rank)
    kw = bm25.get_scores(tokenize(question))
    if max(kw) > 0:
        for rank, i in enumerate(np.argsort(-kw)):
            fused[i] = fused.get(i, 0) + 1 / (60 + rank)
    order = sorted(fused, key=fused.get, reverse=True)[:k]
    return [chunks[i] for i in order], float(dense.max())

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

def calibrate():
    qs = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    rows = [(retrieve(q["question"])[1], q["answerable"], q["id"]) for q in qs]
    ans = [s for s, a, _ in rows if a]
    ref = [s for s, a, _ in rows if not a]
    print(f"Answerable questions : {len(ans)}  similarity min {min(ans):.3f}  max {max(ans):.3f}")
    print(f"Unanswerable questions: {len(ref)}  similarity min {min(ref):.3f}  max {max(ref):.3f}")
    scores = sorted(set(s for s, _, _ in rows))
    best_t, best_acc = None, -1
    for lo, hi in zip(scores, scores[1:]):
        t = (lo + hi) / 2
        acc = sum((s >= t) == a for s, a, _ in rows) / len(rows)
        if acc > best_acc:
            best_t, best_acc = t, acc
    wrong = [qid for s, a, qid in rows if (s >= best_t) != a]
    print(f"\nBest threshold: {best_t:.3f}  (accuracy {best_acc:.2f} on {len(rows)} questions)")
    print("Wrongly handled:", wrong or "none")
    THRESHOLD_FILE.write_text(json.dumps({"threshold": best_t, "accuracy": best_acc}), encoding="utf-8")
    print("Saved", THRESHOLD_FILE)

def answer(question, threshold):
    top, best_sim = retrieve(question)
    if best_sim < threshold:
        return None, best_sim
    return top[0], best_sim

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        calibrate()
        sys.exit()
    if THRESHOLD_FILE.exists():
        threshold = json.loads(THRESHOLD_FILE.read_text())["threshold"]
    else:
        threshold = 0.80
        print("No calibration found. Run 'python ask.py calibrate' first for a better refusal threshold.")
    print("\nAsk a question (type 'exit' to stop).")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("exit", "quit", ""):
            break
        chunk, sim = answer(question, threshold)
        if chunk is None:
            print(f"\nI could not find this in the guideline. (similarity {sim:.2f})")
        else:
            print(f"\nBest matching section (page {chunk['page']}, id {chunk['id']}, similarity {sim:.2f}):\n")
            print(chunk["text"][:700] + ("..." if len(chunk["text"]) > 700 else ""))
        print("\n" + DOC_NOTE)
