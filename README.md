# RAG Backend

FastAPI backend for a document Q&A app. Upload PDF or Markdown files, and ask questions answered from their content. Embeddings use OpenAI, answers come from DeepSeek, and vectors are stored locally in FAISS.

## Requirements

- Python 3.12 (or whichever version you pinned)
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key and a DeepSeek API key (optional)

## Setup

1. Install dependencies:

```bash
   uv sync
```

2. Create a `.env` file in the project root:

```env
   OPENAI_API_KEY=your-openai-key
   DEEPSEEK_API_KEY=your-deepseek-key
```

3. Start the server:

```bash
   uv run python main.py
```

The API runs at `http://localhost:8002`, and the interactive docs are at `http://localhost:8002/docs`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload-pdf` | Upload one or more `.pdf` / `.md` files (multipart form, key `pdfs`) |
| POST | `/chat-response` | Ask a question. Body: `{"user_query": "..."}`. Returns `{"answer": "..."}` |

## Data

Created automatically in the working directory:

- `uploaded_docs/`: original uploaded files
- `faiss_index/`: the vector index, loaded on startup so you don't need to re-upload after a restart

To reset everything, stop the server and delete both folders.

## Notes

- Run a single worker. The index is held in memory per process.
- If you change the embedding model, delete `faiss_index/` and re-upload, since old vectors won't match.