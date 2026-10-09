import os, sys, json, time, csv, re
from pathlib import Path
from google import genai
from google.genai import types
from ask import retrieve, DOC_NOTE          # reuses your best retrieval setup (section chunks + hybrid)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")    # lets Hindi print correctly in the black window

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")   # change with: set GEMINI_MODEL=<name>

if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
    print("No API key found. In this black window run:  set GEMINI_API_KEY=your_key_here")
    print("Then run this script again in the SAME window.")
    sys.exit(1)

if os.environ.get("GEMINI_VERTEX") == "1":
    # for Google Cloud / Vertex AI express-mode keys (these usually start with "AQ.")
    client = genai.Client(vertexai=True, api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
else:
    # for normal Google AI Studio keys (these start with "AIza")
    client = genai.Client()

SYSTEM = """You answer questions about the AICTE Pragati scholarship guidelines using ONLY the context provided.
Rules:
1. If the answer is not stated in the context, reply with exactly NOT_FOUND and nothing else.
2. Answer in the same language as the question (a Hindi question gets a Hindi answer).
3. Keep numbers, amounts and names exactly as written in the context (for example Rs. 8 lakh, 9.5).
4. Be short: 1 to 3 sentences.
5. Do not use outside knowledge and do not guess."""

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

def show_flash_models():
    print("\nModel names available to your key (use one that contains 'flash'):")
    for m in client.models.list():
        if "flash" in m.name:
            print("  ", m.name.replace("models/", ""))
    print("\nThen run:  set GEMINI_MODEL=<name>   and try again.")

def ask_gemini(question):
    top, _ = retrieve(question, k=3)
    context = "\n\n".join(f"[{c['id']} | page {c['page']}]\n{c['text']}" for c in top)
    prompt = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    last_msg = ""
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0))
            return (resp.text or "").strip(), top
        except Exception as e:
            msg = str(e)
            if "404" in msg or "not found" in msg.lower():
                print("Model name problem:", msg[:200])
                show_flash_models()
                sys.exit(1)
            if any(x in msg for x in ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")):
                last_msg = msg
                print(f"  (Gemini said: {msg[:160]} ... waiting 10 seconds, try {attempt + 1} of 3)")
                time.sleep(10)
                continue
            raise
    return "ERROR: Gemini is busy or your free quota is used up. " + last_msg[:120], top

def run_eval():
    qs = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    rows = []
    for q in qs:
        text, _ = ask_gemini(q["question"])
        refused = text.upper().startswith("NOT_FOUND")
        if q["answerable"]:
            correct = (not refused) and any(norm(a) in norm(text) for a in q["answer_contains"])
        else:
            correct = refused
        rows.append({"id": q["id"], "lang": q["lang"], "answerable": q["answerable"],
                     "question": q["question"], "response": text, "correct": correct})
        print(f"{q['id']:4} {'OK ' if correct else 'BAD'} {text[:70]}")
        time.sleep(4)          # stay under the free-tier rate limit
    with open("eval/llm_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    def acc(f):
        sel = [r for r in rows if f(r)]
        return f"{sum(r['correct'] for r in sel)}/{len(sel)}" if sel else "n/a"
    print("\nEnglish answerable :", acc(lambda r: r["answerable"] and r["lang"] == "en"))
    print("Hindi answerable   :", acc(lambda r: r["answerable"] and r["lang"] == "hi"))
    print("Correct refusals   :", acc(lambda r: not r["answerable"]))
    print("Saved eval/llm_results.csv  (open it and read the BAD rows yourself; the check is a simple text match)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "models":
        show_flash_models(); sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_eval(); sys.exit()
    print(f"Using model: {MODEL}\nAsk a question (type 'exit' to stop).")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("exit", "quit", ""):
            break
        text, top = ask_gemini(question)
        if text.upper().startswith("NOT_FOUND"):
            print("\nI could not find this in the guideline.")
        else:
            print("\n" + text)
            print("\nRetrieved from: " + ", ".join(f"{c['id']} (page {c['page']})" for c in top))
        print("\n" + DOC_NOTE)
