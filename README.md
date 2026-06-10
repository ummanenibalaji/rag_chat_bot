# DOCai — Intelligent Document Chatbot

RAG-powered chatbot with React UI. Upload documents, ask questions, analyze images, review CAD drawings, extract array dimensions.

---

## Tech Stack

### Frontend
- React 18 + Vite
- Tailwind CSS v3 (DOCai glassmorphism design system)
- Framer Motion (animations)
- Custom cursor + click-burst canvas effects (`GlobalEffects.jsx`)
- react-markdown + syntax highlighting
- Axios + native fetch (streaming)

### Backend
- FastAPI
- LangChain + LangChain-Ollama + LangChain-Anthropic
- FAISS vector store
- SQLite (auth + sessions)
- JWT (python-jose) + bcrypt

### Models

**Hybrid LLM** — auto-selects provider based on environment:

| Role | Provider | Model |
|------|----------|-------|
| Router (routing + rewriting) | Ollama (always local) | llama3 (configurable) |
| Answer | Claude (if `ANTHROPIC_API_KEY` set) | claude-sonnet-4-6 |
| Answer (fallback) | Ollama | llama3 / gemma3:12b / any |
| Embeddings | HuggingFace | BAAI/bge-base-en-v1.5 (768d) |
| Reranker | HuggingFace | cross-encoder/ms-marco-MiniLM-L-12-v2 |
| Vision | Ollama | gemma3:12b |

### OCR Pipeline
- OpenCV CLAHE → adaptive threshold → deskew
- Tesseract multi-PSM (modes 3, 4, 6, 11)
- Word-level confidence filtering (≥40)
- Table detection via image_to_data
- pdf2image fallback for scanned PDFs (300 DPI)

### RAG Pipeline
- Parent-child chunking (1500/400 chars)
- Hybrid search: MMR + BM25 → Reciprocal Rank Fusion
- Query expansion (synonym-based)
- Cross-encoder reranking with parent context expansion
- Filename-based result prioritization

---

## Features

### Authentication
- Signup / Login with bcrypt password hashing
- JWT tokens with 60-min expiry
- JWT enforced on all upload, ask, and document endpoints
- Per-user file isolation
- Forgot password → Gmail SMTP reset email
- Reset password via token link (auto-detected from URL)
- Password strength indicator (4-bar visual)

### Document Support
- PDF (text + scanned)
- DOCX (paragraphs + tables)
- TXT
- CSV (stats + head preview)
- XLSX (all sheets)
- PPTX
- PNG / JPG / JPEG

### AI Tools

| Tool | Trigger |
|------|---------|
| `array_dimensions` | dimensions, sizes, width, height, measurements of arrays |
| `cad_review` | review, validate, check, QA, error checking, mismatch detection |
| `rag_search` | everything else — summarize, explain, answer questions |
| Calculator | calculate, +, -, *, sqrt |
| Web Search | latest, news, today, stock price |
| Vision AI | image, photo, chart, invoice, screenshot |
| File List | list files, show documents, uploaded files |

### Array Dimension Extraction
- Per-page width/height extracted from CAD PDF embedded text
- Two-pass stacked-fraction reconstruction (e.g. `6 3/8"`)
- Feet-only format support (e.g. `133'`)
- Results rendered as markdown table in chat

### Vision AI
- Auto document type detection (invoice, resume, contract, chart, table, dashboard, screenshot, engineering_drawing)
- Task-specific prompts per document type
- OCR text + visual reasoning combined

### CAD Review
- Engineering drawing QA against PDF pages
- Title block extraction (roof area, array, sheet number)
- Key plan vs drawing mismatch detection

### LLM Management
- `/llm-status` — current router + answer model info
- `/ollama-models` — list available local Ollama models
- `/switch-model` — hot-swap answer model at runtime (authenticated)

### Chat
- Streaming responses (SSE via fetch reader)
- Conversation history across sessions
- Suggestion chips on empty state
- Markdown + syntax-highlighted code blocks
- File-specific or all-files search

---

## Project Structure

```text
backend/
    app.py              # FastAPI routes + LLM management endpoints
    chatbot.py          # RAG orchestration + tool router
    llm_providers.py    # Hybrid LLM (Claude / Ollama), runtime model swap
    auth.py             # JWT + bcrypt
    email_utils.py      # Gmail SMTP password reset
    rag_pipeline.py     # FAISS, BM25, RRF, reranker
    document_loader.py  # PDF/DOCX/CSV/XLSX/PPTX loaders
    ocr_utils.py        # OpenCV + Tesseract OCR pipeline
    vision_utils.py     # Gemma 3 vision + prompt builder
    tools.py            # Calculator, web search
    cad_checker.py      # CAD QA + array dimension extraction

client/
    src/
        api/            # auth.js, chat.js, files.js, client.js
        components/
            Auth/       # LoginPage (login/signup/forgot/reset)
            Chat/       # ChatArea, MessageBubble
            Layout/     # AppLayout, Sidebar (files + conversations)
            UI/         # GlobalEffects (custom cursor, click burst), Spinner
        context/        # AuthContext
    vite.config.js      # Proxy /api → http://127.0.0.1:8000

uploads/
faiss_indexes/
rag_app.db
.env
```

---

## Setup

### 1. Clone

```bash
git clone https://github.com/ummanenibalaji/rag_chat_bot.git
cd rag_chat_bot
```

### 2. Backend — Python env

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install langchain-ollama langchain-huggingface langchain-anthropic \
    pytesseract pillow pymupdf duckduckgo-search pdf2image rank_bm25 \
    python-jose bcrypt python-pptx nltk opencv-python-headless python-dotenv
```

### 3. NLTK data

```python
import nltk
nltk.download('stopwords')
```

### 4. Ollama models

```bash
ollama pull llama3
ollama pull gemma3:12b   # optional, for vision
```

### 5. Environment variables

Create `backend/.env`:

```env
# Auth
JWT_SECRET_KEY=your_secret_key

# Email (password reset)
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# LLM (optional — omit to use Ollama only)
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=auto              # auto | anthropic | ollama
ANTHROPIC_MODEL=claude-sonnet-4-6

# Ollama model overrides (optional)
OLLAMA_ROUTER_MODEL=llama3
OLLAMA_ANSWER_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

> `LLM_PROVIDER=auto` uses Claude if `ANTHROPIC_API_KEY` is set, otherwise falls back to Ollama.
>
> Gmail: use an App Password (Google Account → Security → 2FA → App passwords)

### 6. Frontend — Node

```bash
cd client
npm install
```

---

## Run

### Backend

```bash
cd backend
uvicorn app:app --reload
# → http://127.0.0.1:8000
# → http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd client
npm run dev
# → http://localhost:3000
```

---

## Usage Examples

```text
Summarize this document.
Compare resume.pdf with jd.pdf.
Which employee has Docker experience?
What does this chart show?
Extract invoice details.
Review this CAD drawing for errors.
Give me the array dimensions in a table.
Calculate sqrt(144) + 20%
What's the latest news on AI?
List all uploaded files.
Return result in JSON.
```

---

## Author

Balaji Ummaneni
GitHub: https://github.com/ummanenibalaji
