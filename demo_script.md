# Demo video script (about 2 minutes 30 seconds)

You can narrate in Hindi, English or a mix. The lines below are in simple English so you can say them in your own words. Don't read them word for word.

## Before you record (5 minutes)

1. Start the app in a fresh black window: set your key and model, then `python -m streamlit run app.py`.
2. **Warm up:** click each of the 4 example questions once so the answers are remembered and show up instantly.
3. Open `README.md` in another tab (or a slide) showing the results table.
4. Close other programs, turn off notifications, and make the browser zoom about 110%.
5. Never show your API key or the black window with `set GEMINI_API_KEY=...` typed in it.

## Timeline

### 0:00 - 0:20 | The problem (show the app title)
"Scholarship rules are hidden in long English PDFs. Many students and families can't easily find simple answers like the income limit or the yearly amount. A normal chatbot can invent numbers, and that's risky when money and eligibility are involved."

### 0:20 - 0:40 | The idea
"I built a scholarship assistant for the AICTE Pragati scholarship. It answers only from the official guideline, shows its source, works in English and Hindi, and refuses when the answer isn't in the document."

### 0:40 - 1:30 | Live demo (the main part)
1. Click **"What is the family income limit?"**
   "It answers: Rs. 8 lakh per annum. Let me open the sources." *(expand "Sources used")* "These are the exact sections from the PDF, with page numbers, so anyone can check the answer."
2. Click the **Hindi example** (scholarship amount per year).
   "Now a Hindi question. It answers in Hindi, with the amount Rs. 50,000 per year."
3. Click **"What is the last date to apply this year?"**
   "This isn't in the document. Instead of guessing a date, it says it could not find it. That's the most important safety feature."
4. Point to the blue note at the bottom.
   "It also tells you the document is from 2020-21 and that rules may have changed."

### 1:30 - 2:05 | How I know it works (show the README results table)
"I didn't just build a demo. I tested it with 33 questions, in English and Hindi, including questions the document can't answer. I compared three search methods and two ways of cutting up the document."
"Keyword search failed on Hindi questions, scoring 0.25. Embedding-based search reached 1.0 on the Hindi questions, and combining both methods, with the document cut by section, worked best."
*(Then give your end-to-end Gemini scores from the README, using your real numbers.)*

### 2:05 - 2:30 | Limits and next steps
"It currently covers one document, the 2020-21 version, and my test set is small, especially in Hindi. Next I would add the other scholarship schemes and newer guidelines, and an eligibility checker where you enter your details and get matching schemes with sources."
"Thank you."

## Tips

- If an answer is slow, don't wait on camera. Warm up first, or cut the pause when you edit.
- Keep your voice calm and speak a little slower than normal.
- A phone screen recorder or the Windows screen recorder (**Win + G**) is enough. You don't need to edit anything fancy.
- Upload the video as unlisted or attach it directly, and **test the link** before submitting.
