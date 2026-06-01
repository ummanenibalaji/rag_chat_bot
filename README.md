# AI-Powered Document Chatbot

An intelligent RAG (Retrieval-Augmented Generation) chatbot that allows users to upload documents, images, and presentations, then ask questions using natural language.

---

## Features

### Authentication
- User Signup
- User Login
- Persistent Sessions

### Document Support
- PDF
- DOCX
- TXT
- CSV
- XLSX
- PPTX
- PNG
- JPG
- JPEG

### AI Capabilities
- Hybrid Retrieval (FAISS + BM25)
- Query Rewriting
- Reranking
- Multi-Document Search
- File-Specific Search
- Document Comparison
- Vision AI
- OCR Support
- JSON Output on Request

### Tools
- Calculator Tool
- Web Search Tool
- Vision Analysis Tool

---

## Tech Stack

### Backend
- FastAPI
- LangChain
- FAISS
- Sentence Transformers
- Ollama
- SQLite

### Frontend
- Streamlit

### Models
- Llama 3
- Gemma 3 12B
- all-MiniLM-L6-v2
- cross-encoder/ms-marco-MiniLM-L-6-v2

---

## Project Structure

```text
backend/
    app.py
    chatbot.py
    auth.py
    document_loader.py
    rag_pipeline.py
    vector_store.py

frontend/
    app.py

uploads/
faiss_indexes/
rag_app.db
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/ummanenibalaji/rag_chat_bot.git

cd rag_chat_bot
```

### Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Install Additional Dependencies

```bash
pip install python-docx
pip install pandas
pip install openpyxl
pip install python-pptx
```

---

## Install Ollama

Download and install Ollama:

https://ollama.com

Pull required models:

```bash
ollama pull llama3
ollama pull gemma3:12b
```

Verify:

```bash
ollama list
```

---

## Run Backend

```bash
cd backend

uvicorn app:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## Run Frontend

Open a new terminal:

```bash
source venv/bin/activate

cd frontend

streamlit run app.py
```

Frontend:

```text
http://localhost:8501
```

---

## Usage

### Upload Documents

Supported:

- PDF
- DOCX
- TXT
- CSV
- XLSX
- PPTX
- PNG
- JPG
- JPEG

### Ask Questions

Examples:

```text
What skills are mentioned?

Summarize the document.

Compare resume.pdf and jd.pdf.

Which employee knows Docker?

Return the result in JSON.
```

---

## Search Modes

### All Files

Searches across every uploaded document.

### File Specific

Search only within the selected file.

### Multi-File Comparison

Compare multiple uploaded documents.

---

## Vision AI Examples

```text
What does this image contain?

Analyze this chart.

Extract information from this screenshot.
```

---

## Future Roadmap

- Streaming Responses
- Download JSON Reports
- Download PDF Reports
- Advanced Vision AI
- Workspaces
- Admin Dashboard

---

## Author

Balaji Ummaneni

GitHub:
https://github.com/ummanenibalaji
