import os
import streamlit as st

st.set_page_config(page_title="Pragati Scholarship Assistant", page_icon="🎓")
st.title("🎓 AICTE Pragati Scholarship Assistant")
st.caption("Ask in English or Hindi. Answers come only from the official guideline document.")

if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
    st.error("No API key found. Close this app, run  set GEMINI_API_KEY=your_key  in the black window, then start the app again from the same window.")
    st.stop()

with st.spinner("Loading search model (first time takes a little while)..."):
    import ask_llm                      # loads retrieval model once, then it stays in memory

@st.cache_data(show_spinner=False)
def cached_answer(q):
    # repeated questions (like your demo examples) come back instantly
    text, top = ask_llm.ask_gemini(q)
    if text.startswith("ERROR"):
        raise RuntimeError(text)      # errors are raised so they are NOT remembered
    return text, top

EXAMPLES = [
    "What is the family income limit?",
    "How many scholarships are allotted to Bihar?",
    "छात्रवृत्ति की राशि प्रति वर्ष कितनी है?",
    "What is the last date to apply this year?",
]

if "question" not in st.session_state:
    st.session_state.question = ""

st.write("Try an example:")
cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    if cols[i % 2].button(ex, key=f"ex{i}"):
        st.session_state.question = ex

question = st.text_input("Your question", key="question")

if question.strip():
    try:
        with st.spinner("Searching the guideline..."):
            text, top = cached_answer(question.strip())
    except SystemExit:
        st.error("The model name was not accepted. See the black window for the list of available models.")
        st.stop()
    except Exception as e:
        st.error("Gemini is busy or your free quota is used up. Wait 1-2 minutes and ask again. "
                 f"(Details: {str(e)[:200]})")
        st.stop()

    if text.upper().startswith("NOT_FOUND"):
        st.warning("I could not find this in the guideline, so I won't guess.")
    else:
        st.success(text)

    with st.expander("Sources used (sections retrieved from the PDF)"):
        for c in top:
            st.markdown(f"**{c['id']}** (page {c['page']})")
            st.write(c["text"][:600] + ("..." if len(c["text"]) > 600 else ""))

st.info(ask_llm.DOC_NOTE)
