"""RAG Document Chat — Gradio UI (entry point for Hugging Face Spaces)."""
import os
import gradio as gr

try:  # optional: load a local .env during development (no-op on Spaces)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rag import pipeline, llm

ALLOWED_EXT = [".pdf", ".docx", ".txt"]
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --- Built-in corpus (Constitution of India), indexed once at startup ---
DEFAULT_STORE = None
DEFAULT_STATUS = ""


def _default_doc_paths():
    if not os.path.isdir(DATA_DIR):
        return []
    return sorted(
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXT
    )


def init_default_store():
    """Build the built-in index once. Failures are non-fatal (upload still works)."""
    global DEFAULT_STORE, DEFAULT_STATUS
    paths = _default_doc_paths()
    if not paths:
        return
    try:
        DEFAULT_STORE, summaries = pipeline.build_index(paths)
        names = ", ".join(n for n, _ in summaries)
        DEFAULT_STATUS = (
            f"📚 **Built-in corpus loaded:** Constitution of India — {names}. "
            "Ask a question below, or upload your own files to use them instead."
        )
    except Exception as e:
        DEFAULT_STATUS = f"⚠️ Could not load the built-in corpus: {e}"


def process_files(files):
    """Build a session-scoped index from uploaded files."""
    if not files:
        return None, "Please upload at least one PDF, DOCX, or TXT file."
    paths = [getattr(f, "name", f) for f in files]  # works for str or file obj

    bad = [os.path.basename(p) for p in paths
           if os.path.splitext(p)[1].lower() not in ALLOWED_EXT]
    if bad:
        return None, f"❌ Unsupported file(s): {', '.join(bad)}. Allowed: PDF, DOCX, TXT."

    try:
        store, summaries = pipeline.build_index(paths)
    except Exception as e:  # surface a clean message to the user
        return None, f"❌ {e}"

    total = sum(c for _, c in summaries)
    lines = "\n".join(f"- **{n}** — {c} chunks" for n, c in summaries)
    status = (
        f"✅ Indexed {len(summaries)} document(s) into {total} chunks.\n{lines}\n\n"
        "You can start asking questions."
    )
    return store, status


def chat_fn(message, history, store):
    """Handle a chat turn; history uses the OpenAI-style messages format."""
    message = (message or "").strip()
    if not message:
        return history, ""

    active = store if (store is not None and len(store)) else DEFAULT_STORE
    if active is None or len(active) == 0:
        reply = "Please upload and process documents before asking questions."
    else:
        reply, hits = pipeline.answer(active, message, history=history)
        if hits and reply != pipeline.OUT_OF_SCOPE_MSG and reply != pipeline.INJECTION_MSG:
            sources = sorted({h["source"] for h in hits})
            reply += f"\n\n*Sources: {', '.join(sources)}*"

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    return history, ""


# Build the built-in index at startup so DEFAULT_STATUS is ready for the UI.
init_default_store()

with gr.Blocks(title="RAG Document Chat") as demo:
    gr.Markdown(
        "# 📄 RAG Document Chat\n"
        "Ask questions answered strictly from document content, with guardrails "
        "for prompt injection and out-of-scope questions. This demo comes preloaded "
        "with the **Constitution of India** (Fundamental Rights, Directive Principles, "
        "Fundamental Duties) — try a question right away, or upload your own "
        "PDF / DOCX / TXT files."
    )

    store_state = gr.State(None)  # per-session vector store (overrides built-in)

    with gr.Row():
        with gr.Column(scale=1):
            files = gr.File(
                label="Upload your own documents (optional)",
                file_count="multiple",
                file_types=ALLOWED_EXT,
                type="filepath",
            )
            process_btn = gr.Button("Process documents", variant="primary")
            status = gr.Markdown(DEFAULT_STATUS)
            if not llm.is_configured():
                gr.Markdown(
                    "⚠️ **No LLM API key detected.** Set `GROQ_API_KEY` "
                    "(or configure another provider) to enable answering."
                )

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat", height=460)
            msg = gr.Textbox(
                placeholder="e.g. What does Article 21 protect?",
                show_label=False,
                autofocus=True,
            )
            with gr.Row():
                send = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear chat")

    process_btn.click(process_files, inputs=[files], outputs=[store_state, status])
    send.click(chat_fn, inputs=[msg, chatbot, store_state], outputs=[chatbot, msg])
    msg.submit(chat_fn, inputs=[msg, chatbot, store_state], outputs=[chatbot, msg])
    clear.click(lambda: [], outputs=[chatbot])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
