# Pragati Scholarship Assistant

**A bilingual (English + Hindi), source-grounded question-answering system for the AICTE Pragati Scholarship (Degree) guidelines, built with a careful retrieval evaluation.**

ML Empowerment Hackathon submission · Author: **[YOUR NAME]**

---

## 1. Problem

Eligibility rules, amounts and deadlines for scholarships are buried in long PDFs, mostly in English. Students and families who are more comfortable in Hindi often cannot find a simple answer such as "Is my family income too high?" or "How much money is given per year?"

A general chatbot can answer from memory, but in a money-and-eligibility setting an invented amount or date can mislead someone. So this project has three rules:

1. Answer **only** from the official document.
2. **Show the source** for every answer.
3. **Refuse** instead of guessing when the document does not contain the answer.

## 2. What it does

- Accepts questions in **English or Hindi**.
- Finds the relevant sections of the guideline PDF and answers briefly in the language of the question.
- Shows the retrieved sections (with page numbers) so the user can verify the answer.
- Says *"I could not find this in the guideline, so I won't guess"* when the answer is not in the document.
- Always shows the document date, because rules change.

| English answer | Hindi answer | Refusal (not in document) |
|---|---|---|
| ![English](screenshots/english_income_limit.png) | ![Hindi](screenshots/hindi_scholarship_amount.png) | ![Refusal](screenshots/refusal_last_date.png) |

## 3. How it works

1. **Extract** the text of the guideline PDF with PyMuPDF, keeping page numbers.
2. **Chunk** the text in two ways, so they can be compared:
   - *Section chunks:* one chunk per numbered section plus the annexure (12 chunks).
   - *Fixed chunks:* 120-word windows with 30 words of overlap (15 chunks).
3. **Retrieve** with three methods, so they can be compared:
   - *BM25* keyword search.
   - *Dense* embeddings with `multilingual-e5-small` (understands Hindi and English).
   - *Hybrid*: BM25 and Dense rankings combined with reciprocal rank fusion.
4. **Generate** the answer with Gemini (`gemini-3.5-flash-lite`). The top 3 sections are passed in, with strict instructions: use only the context, return `NOT_FOUND` if the answer is absent, answer in the user's language, and keep numbers exactly as written.
5. **Serve** through a Streamlit web app that shows the answer, the sources and the document date.

## 4. Evaluation

**Test set** (`eval/questions.json`): 33 questions: 25 English, 4 Hindi and 4 that the document cannot answer. Every answerable question has a required answer string (for example "8 lakh"). A retrieval **hit@k** means that string appears in at least one of the top *k* retrieved chunks.

### 4.1 Retrieval results

| Chunking | Retriever | English hit@1 | English hit@3 | Hindi hit@1 | Hindi hit@3 |
|---|---|---|---|---|---|
| Section | BM25 | 0.88 | 1.00 | 0.25 | 0.25 |
| Section | Dense | 0.80 | 0.96 | 1.00 | 1.00 |
| Section | **Hybrid** | 0.88 | **1.00** | 1.00 | **1.00** |
| Fixed | BM25 | 0.92 | 1.00 | 0.25 | 0.25 |
| Fixed | Dense | 0.76 | 0.84 | 0.50 | 0.50 |
| Fixed | Hybrid | 0.80 | 0.92 | 0.50 | 0.50 |

(English n = 25, Hindi n = 4. Raw numbers: `eval/results_all.csv`.)

**Findings**

- **Hindi needs embeddings.** Keyword search scored 0.25 on Hindi questions because it only matches exact words. With section chunks, Dense and Hybrid reached 1.00.
- **Section chunks beat fixed chunks** for embedding-based retrieval (English hit@3 0.96 vs 0.84 for Dense; Hindi 1.00 vs 0.50). Splitting at the document's natural sections keeps related facts together.
- **Hybrid with section chunks is the best setup.** It reached 1.00 hit@3 in both languages. Dense alone missed one English question (the refund rule, q18) that Hybrid recovered.
- A bug caught during development: when a query matched nothing, the keyword search returned the first chunks by default, which made Hindi results look better than they were. It was fixed so that no match returns nothing, and all numbers above use the fixed version.

### 4.2 End-to-end answer results (Gemini)

| Question group | Correct | Total |
|---|---|---|
| English, answerable | **[FILL IN]** | 25 |
| Hindi, answerable | **[FILL IN]** | 4 |
| Correctly refused (not in document) | **[FILL IN]** | 4 |

An answer counts as correct if it contains the required answer string, and a refusal counts as correct if the model returns `NOT_FOUND`. This is a simple text match, so a correct answer worded differently can be marked wrong. Every failed row in `eval/llm_results.csv` was therefore read by hand: **[FILL IN: how many were real mistakes and how many were only wording differences]**.

### 4.3 Error analysis

- **Fixed chunks split related facts.** With fixed chunks, Dense and Hybrid missed simple questions such as the income limit (q01) and Bihar's scholarship count (q05), because the eligibility text and the annexure table were cut into pieces.
- **Keyword search cannot cross languages.** It missed three of the four Hindi questions (h01 to h03). The fourth only matched because it contains the English word "CGPA".
- **Dense alone is weaker on exact rules.** It missed the refund rule (q18) on section chunks, likely because that rule sits inside a long section with many other rules. Adding keyword search fixed it.
- **Refusal works on a clear case.** "What is the last date to apply this year?" is correctly refused, because the 2020-21 document has no deadline for the current year.

## 5. Limitations

- **One document, and an old one.** It covers only the 2020-21 Pragati (Degree) guidelines (July 2020). Amounts, income limits and rules may have changed, so the app shows the document date with every answer. Always check the official portal before applying.
- **Small test set.** 33 questions, only 4 of them in Hindi, all from a single document. Many were written close to the document's own wording, which favours keyword search. The Hindi result (1.00 vs 0.25) is a strong signal but not statistically solid.
- **Rough metrics.** Retrieval hit@k checks only that the answer text was retrieved, not that the final answer is right. The end-to-end check is a text match plus manual review.
- **Free-tier limits.** Gemini's free quota was exhausted during testing, which is why a lighter model was used.
- **Not official advice.** This is a student project. It does not replace the official guidelines or the National Scholarship Portal.

## 6. Future work

- Add the other schemes (Pragati Diploma, Saksham, and others) and their latest versions, and flag outdated documents automatically.
- Build an eligibility checker: a short form (income, year of study, state) that returns the schemes a student likely qualifies for, with sources.
- Grow the test set with questions written by real students, including more Hindi and mixed Hindi-English questions, and evaluate answer correctness with human review.
- Read tables (such as the state-wise annexure) more reliably, and try re-ranking of retrieved chunks.

## 7. How to run

Windows, Python 3.10 or newer.

```
pip install -r requirements.txt

python extract.py          # PDF -> text            (data/raw -> data/clean)
python chunk.py            # text -> chunks
python evaluate_all.py     # retrieval comparison -> eval/results_all.csv

set GEMINI_API_KEY=your_key_here        # key is NOT stored in any file
set GEMINI_MODEL=gemini-3.5-flash-lite
python ask_llm.py eval     # end-to-end test -> eval/llm_results.csv
python -m streamlit run app.py          # web demo
```

The first run downloads the embedding model (about 470 MB). Put the guideline PDF at `data/raw/pragati_degree_2020-21.pdf` (source: AICTE, July 2020).

## 8. Files

| File | Purpose |
|---|---|
| `extract.py` | Extracts text from the PDF, with page numbers |
| `chunk.py` | Creates section chunks and fixed-size chunks |
| `search.py` | BM25 keyword search |
| `evaluate_all.py` | Compares BM25, Dense and Hybrid on both chunk types |
| `ask.py` | Retrieval used by the app (section chunks + hybrid) |
| `ask_llm.py` | Gemini answer generation, refusals and the end-to-end test |
| `app.py` | Streamlit web demo |
| `eval/questions.json` | The 33-question test set |
| `eval/results_all.csv`, `eval/llm_results.csv` | Evaluation results |
