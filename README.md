# DocuMind AI — Intelligent Document Chatbot

RAG-powered chatbot with React UI. Upload documents, ask questions, analyze images, review CAD drawings.

---

## Tech Stack

### Frontend
- React 18 + Vite
- Tailwind CSS v3 (glassmorphism design)
- Framer Motion (animations)
- react-markdown + syntax highlighting
- Axios + native fetch (streaming)

### Backend
- FastAPI
- LangChain + LangChain-Ollama
- FAISS vector store
- SQLite (auth + sessions)
- JWT (python-jose) + bcrypt

### Models
- **LLM:** Llama 3 (chat), Gemma 3 12B (vision)
- **Embeddings:** BAAI/bge-base-en-v1.5 (768d)
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-12-v2

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
| Tool | Trigger Keywords |
|------|-----------------|
| Calculator | calculate, +, -, *, sqrt |
| Web Search | latest, news, today, stock price |
| Vision AI | image, photo, chart, invoice, screenshot |
| CAD Review | cad, drawing, blueprint, site plan, title block |
| File List | list files, show documents, uploaded files |

### Vision AI
- Auto document type detection (invoice, resume, contract, chart, table, dashboard, screenshot, engineering_drawing)
- Task-specific prompts per document type
- OCR text + visual reasoning combined

### CAD Review
- Engineering drawing QA against PDF pages
- Title block extraction (roof area, array, sheet number)
- Key plan vs drawing mismatch detection

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
    app.py              # FastAPI routes
    chatbot.py          # RAG orchestration + tool router
    auth.py             # JWT + bcrypt
    email_utils.py      # Gmail SMTP password reset
    rag_pipeline.py     # FAISS, BM25, RRF, reranker
    document_loader.py  # PDF/DOCX/CSV/XLSX/PPTX loaders
    ocr_utils.py        # OpenCV + Tesseract OCR pipeline
    vision_utils.py     # Gemma 3 vision + prompt builder
    tools.py            # Calculator, web search, CAD review
    cad_checker.py      # CAD marker safety layer

client/
    src/
        api/            # auth.js, chat.js, client.js
        components/
            Auth/       # LoginPage (login/signup/forgot/reset)
            Chat/       # ChatArea, MessageBubble
            Layout/     # Sidebar (files + conversations)
            UI/         # Spinner
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
pip install langchain-ollama langchain-huggingface pytesseract pillow \
    pymupdf duckduckgo-search pdf2image rank_bm25 python-jose bcrypt \
    python-pptx nltk opencv-python-headless
```

### 3. NLTK data

```python
import nltk
nltk.download('stopwords')
```

### 4. Ollama models

```bash
ollama pull llama3
ollama pull gemma3:12b
```

### 5. Environment variables

Create `backend/.env`:

```env
JWT_SECRET_KEY=your_secret_key
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

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
Calculate sqrt(144) + 20%
What's the latest news on AI?
List all uploaded files.
Return result in JSON.
```

---

## Author

Balaji Ummaneni
GitHub: https://github.com/ummanenibalaji
