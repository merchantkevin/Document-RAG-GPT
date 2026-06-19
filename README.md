---
title: RAG Document Chat
emoji: 📄
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.16.0
app_file: app.py
pinned: false
license: mit
---

# 📄 RAG Document Chat

A Retrieval-Augmented Generation (RAG) chat application. Ask questions answered
**strictly from document content**, with guardrails against prompt injection and
out-of-scope queries. The app ships **preloaded with the Constitution of India**
so it works immediately, and you can also upload your own PDF, DOCX, or TXT files.

## Built-in dataset

On startup the app indexes a small India-relevant corpus (in `data/`):

- `Fundamental-Rights.pdf` — Part III, Articles 12–35
- `Directive-Principles.docx` — Part IV, Articles 36–51
- `Preamble-and-Fundamental-Duties.txt` — Preamble and Article 51A

This exercises all three file loaders (PDF, DOCX, TXT). The bare text of the
Constitution is freely reproducible in India (Copyright Act, 1957, s. 52); it was
compiled from public sources via `build_corpus.py` and is provided for
demonstration (see `indiacode.nic.in` for the authoritative current text).

Sample questions: *"What does Article 21 protect?"*, *"What is the right against
exploitation?"*, *"List the Fundamental Duties"*, *"What does the Preamble say?"*.
An out-of-scope question like *"What's the weather today?"* is correctly refused.

## Document scope (by design)

The assistant answers from one document set at a time:

- **Default:** the built-in Constitution of India corpus described above.
- **After upload:** once you upload and process your own files, the system uses
  **only** those documents for the rest of the session; the built-in corpus is no
  longer searched.

This single-source behaviour is an intentional design choice — when a user brings
their own documents, answers should be grounded **solely** in those documents,
with no blending from an unrelated default corpus. Starting a new session (or
restarting the Space) reverts to the built-in corpus.

## Features

- **Multi-format upload** — PDF, DOCX (paragraphs + tables), and TXT.
- **RAG pipeline** — chunking → embeddings → vector search → grounded generation.
- **Guardrails**
  - Input validation (empty / too-short / too-long).
  - Direct prompt-injection detection on the user's query.
  - Indirect prompt-injection defence: retrieved text is passed to the model as
    clearly delimited, *untrusted* data that it is instructed never to obey.
  - Out-of-scope handling: if retrieval similarity is below a threshold, the app
    answers "I couldn't find that in the uploaded documents" without calling the LLM.
- **Session isolation** — each user's index lives in their own session state.
- **Provider-agnostic LLM** — Groq (default, free tier), OpenAI, or Gemini, all via
  the OpenAI-compatible API.

## How it works

1. **Load** documents and extract text (`pypdf`, `python-docx`).
2. **Chunk** text into ~900-character, paragraph-aware pieces with overlap.
3. **Embed** chunks with `all-MiniLM-L6-v2` (Sentence-Transformers), normalized.
4. **Store** vectors in an in-memory FAISS index (`IndexFlatIP` = cosine similarity).
5. **Answer**: validate → injection check → retrieve top-k → scope check →
   generate a grounded answer from the retrieved excerpts only.

## Project structure

```
app.py                 # Gradio UI + orchestration (loads built-in corpus at startup)
build_corpus.py        # (dev) regenerates the data/ files from public sources
data/                  # built-in corpus: Constitution of India (PDF, DOCX, TXT)
rag/
  document_loader.py   # PDF / DOCX / TXT extraction + validation
  chunker.py           # paragraph-aware chunking with overlap
  embeddings.py        # Sentence-Transformers wrapper (lazy singleton)
  vector_store.py      # FAISS in-memory store
  llm.py               # OpenAI-compatible client (Groq/OpenAI/Gemini)
  guardrails.py        # input validation + injection detection
  pipeline.py          # build_index() and answer()
requirements.txt
.env.example
```

## Local setup

```bash
git clone <your-repo-url>
cd rag-document-chat
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env       # then edit .env and add your API key
python app.py              # opens at http://127.0.0.1:7860
```

### Getting a free API key (Groq)

Create one at <https://console.groq.com/keys> (free tier, no credit card), then set
`GROQ_API_KEY` in `.env`. To use a different provider, set `LLM_PROVIDER` to
`openai` or `gemini` and provide the matching key.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq`, `openai`, or `gemini` |
| `GROQ_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | — | key for the chosen provider |
| `LLM_MODEL` | provider default | override the model name |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | embedding model |
| `RELEVANCE_THRESHOLD` | `0.25` | min cosine score to treat a match as in-scope |

## Deploy to Hugging Face Spaces

1. Create a new Space at <https://huggingface.co/new-space> — choose **Gradio** as the SDK.
2. Push this repository to the Space (or upload the files). The included README
   front matter sets `sdk: gradio` and `app_file: app.py`. *If the build reports
   the SDK version is unavailable, change `sdk_version` to the latest 6.x shown in
   the Space settings and update `gradio==` in `requirements.txt` to match.*
3. In **Settings → Variables and secrets**, add a secret named `GROQ_API_KEY`
   (and `LLM_PROVIDER` if not using Groq).
4. The Space builds automatically and serves the app.

## Notes & limitations

- The index is in memory and resets when the Space restarts or the session ends.
- Scanned/image-only PDFs yield no text (no OCR); the app reports this clearly.
- The injection filter uses high-signal heuristics; the model-side instruction is
  the primary defence against instructions hidden inside documents.
