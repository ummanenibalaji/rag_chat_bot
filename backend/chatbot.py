import os
import re
import json

from document_loader import (
    load_document
)

from langchain_community.vectorstores import (
    FAISS
)


from llm_providers import router_llm

from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from rag_pipeline import (
    create_bm25_retriever,
    hybrid_search,
    rerank_documents
)

from tools import (
    calculator_tool,
    web_search_tool,
    vision_tool,
    cad_review_tool
)

from cad_checker import (
    extract_array_dimensions
)


# =====================================================
# CAD MARKER SAFETY LAYER
# =====================================================

def check_cad_markers(
    pdf_path
):
    """
    Verify CAD document before running expensive OCR.
    
    Looks for engineering-specific markers in the preview.
    """
    
    try:
        loader = PyPDFLoader(
            pdf_path
        )
        
        docs = loader.load()
        
        preview = ""
        
        for page in docs[:2]:
            preview += (
                page.page_content[:2000].lower()
                + "\n\n"
            )
        
        # CAD-specific markers
        cad_markers = [
            "roof area",
            "array layout",
            "key plan",
            "engineer's stamp",
            "sheet sm.",
            "title block",
            "drawing number",
            "revision",
            "scale",
            "grid reference",
            "electrical diagram",
            "wiring diagram",
            "schematic",
            "blueprint",
            "cad",
            "autocad",
            "revit",
            "drawing",
            "design",
            "engineering drawing",
            "technical drawing"
        ]
        
        score = sum(
            marker in preview
            for marker in cad_markers
        )
        
        return score >= 3
        
    except Exception as e:
        print(
            f"Error checking CAD markers: {e}"
        )
        return False


# =====================================================
# ENHANCED LLM ROUTER (JSON OUTPUT)
# =====================================================

def llm_route(
    query,
    pdf_path
):
    """
    Route user intent to appropriate tool.
    
    Returns JSON with tool, confidence, and reason.
    """

    try:
        loader = PyPDFLoader(
            pdf_path
        )

        docs = loader.load()

        preview = ""

        for page in docs[:2]:

            preview += (
                page.page_content[:1500]
                + "\n\n"
            )

    except Exception as e:
        print(
            f"Error loading PDF: {e}"
        )
        return {
            "tool": "rag_search",
            "confidence": 0.5,
            "reason": "Could not preview document, using general RAG"
        }

    prompt = f"""
You are an intelligent AI router for a document assistant.

Think carefully about what the user wants, then pick the best tool.

Available tools:

1. array_dimensions
   → Use when the user wants dimensions, sizes, widths, heights, measurements of arrays
   → Examples: "give dimensions", "tell me the dimensions", "what are the sizes",
     "dimensions in a table", "how wide/tall are the arrays", "dimensions in detail"

2. cad_review
   → Use ONLY when the user explicitly wants a QA check, review, error validation,
     or mismatch detection on the drawing
   → Examples: "review the drawing", "check for errors", "find mismatches",
     "validate the CAD", "QA check"
   → Do NOT use for general dimension or description queries

3. rag_search
   → Use for everything else: summarize, describe, explain, answer questions,
     key points, what is this document about, general analysis

Think step by step:
- What is the user literally asking for?
- Does this need dimension extraction, a QA review, or a general answer?

User Query: {query}

Document Preview:
{preview}

Return ONLY valid JSON (no markdown, no code fence):

{{
    "tool": "array_dimensions" or "cad_review" or "rag_search",
    "confidence": 0.0 to 1.0,
    "reason": "one sentence explanation of your reasoning"
}}
"""

    response = llm.invoke(
        prompt
    )

    response_text = (
        response.content
        .strip()
    )
    
    # Handle markdown code fences
    if "```json" in response_text:
        response_text = response_text.split(
            "```json"
        )[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split(
            "```"
        )[1].split("```")[0].strip()
    
    try:
        decision = json.loads(
            response_text
        )
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        print(
            f"JSON parse error: {response_text}"
        )
        decision = {
            "tool": "rag_search",
            "confidence": 0.5,
            "reason": "Could not parse router response"
        }
    
    # ----- SAFETY LAYER -----
    # Even if router says cad_review,
    # verify it's actually a CAD document
    if decision.get("tool") == "cad_review":
        
        is_cad = check_cad_markers(
            pdf_path
        )
        
        if not is_cad:
            print(
                "SAFETY CHECK FAILED: "
                "Document doesn't contain CAD markers"
            )
            decision["tool"] = "rag_search"
            decision["confidence"] = (
                decision.get("confidence", 0.7) * 0.6
            )
            decision["reason"] = (
                "Document lacks CAD markers. "
                "Using general RAG instead."
            )
    
    print(
        "LLM ROUTER DECISION:"
    )
    print(
        json.dumps(
            decision,
            indent=2
        )
    )

    return decision

# =====================================================
# LLM (router — local Ollama, fast)
# Answer LLM is in llm_providers.answer_llm
# =====================================================

llm = router_llm


# =====================================================
# LOAD USER VECTOR STORE
# =====================================================

def load_user_vector_store(
    user_id
):

    from rag_pipeline import embeddings

    vector_path = (
        f"faiss_indexes/user_{user_id}"
    )

    if not os.path.exists(
        vector_path
    ):

        return None

    vector_store = FAISS.load_local(
        vector_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


# =====================================================
# LOAD ALL DOCUMENT CHUNKS
# =====================================================

def load_all_chunks(
    user_id
):

    upload_folder = (
        f"uploads/user_{user_id}"
    )

    documents = []

    if not os.path.exists(
        upload_folder
    ):

        return []

    for filename in os.listdir(
        upload_folder
    ):

        file_path = os.path.join(
            upload_folder,
            filename
        )

        # -------------------------------------------------
        # PDF DOCUMENTS
        # -------------------------------------------------

        try:

            docs = load_document(
                file_path
            )

            for doc in docs:

                doc.metadata["source"] = (
                    filename
                )

            documents.extend(
                docs
            )

        except Exception as e:

            print(
                f"Failed loading {filename}: {e}"
            )

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    )

    chunks = splitter.split_documents(
        documents
    )

    print("\nDOCUMENTS LOADED:", len(documents))
    print("CHUNKS CREATED:", len(chunks))

    for doc in documents:

        print(
            "SOURCE:",
            doc.metadata.get(
                "source"
            )
        )
    return chunks

# =====================================================
# DETECT TOOL
# Fast-path for high-confidence cases.
# Ambiguous document queries go to the LLM router.
# =====================================================

def detect_tool(query):

    query_lower = query.lower()

    # Array dimensions — any mention of dimension/size/width/height
    # in the context of arrays or drawings is unambiguous in this app
    dimension_words = [
        "dimension", "dimensions", "array width", "array height",
        "width of array", "height of array", "array size", "array sizes",
        "array measurements", "give the dimensions", "give me the dimensions",
        "tell the dimensions", "tell me the dimensions",
        "show the dimensions", "show me the dimensions",
        "what are the dimensions", "find the dimensions",
        "extract dimensions", "dimensions of the array",
        "dimensions of array", "dimensions of all",
        "dimensions per page", "dimensions from",
        "dimensions in", "overall dimensions",
    ]
    if any(k in query_lower for k in dimension_words):
        return "array_dimensions"

    # Explicit CAD review / QA requests
    review_keywords = [
        "review the drawing", "review the array", "review array",
        "review the cad", "review cad", "review this document",
        "review the document", "check for errors", "find errors",
        "find mismatches", "validate the drawing", "validate the array",
        "qa check", "drawing qa", "drawing review", "cad review",
        "check drawing", "check the array", "check array",
        "array mismatch", "sheet mismatch", "review cad",
        "validate cad", "error check", "check for mismatch",
        "verify the array", "verify array"
    ]
    if any(k in query_lower for k in review_keywords):
        return "cad_review"

    # Pure math — unambiguous
    math_keywords = ["calculate", "sqrt", "square root"]
    math_symbols = re.compile(r'\d+\s*[\+\-\*\/\%]\s*\d+')
    if math_symbols.search(query_lower) or any(k in query_lower for k in math_keywords):
        return "calculator"

    # Explicit real-time web lookups
    web_keywords = [
        "stock price", "today's news", "latest news",
        "search the web", "search online", "look it up online"
    ]
    if any(k in query_lower for k in web_keywords):
        return "web_search"

    # Explicit image analysis
    image_keywords = [
        "analyze this image", "describe this image",
        "what's in this image", "what is in this image",
        "read text from image", "extract text from image"
    ]
    if any(k in query_lower for k in image_keywords):
        return "vision"

    # Explicit file listing
    file_keywords = [
        "list my documents", "list my files",
        "what documents do i have", "what files do i have",
        "show my files", "show my documents",
        "uploaded files", "uploaded documents",
        "what files are uploaded", "what documents are uploaded"
    ]
    if any(k in query_lower for k in file_keywords):
        return "file_list"

    # Everything else → LLM router decides
    return None


# =====================================================
# SUMMARIZE QUERY DETECTION
# =====================================================

_SUMMARIZE_KEYWORDS = [
    "summarize", "summary", "overview", "tell me about", "what is this",
    "describe", "key points", "main points", "highlights", "brief",
    "what does this document", "what is in this", "give me an overview",
    "explain this document", "what is the document about",
    "who is this", "what are the key", "what are the main",
    # section-specific broad retrieval
    "from the", "in the", "section", "all instruction", "all the instruction",
    "list all", "list the", "give all", "give me all", "what are all",
    "latest instruction", "latest information", "most recent instruction",
    "recent instruction", "other information", "other instruction",
    "all entries", "all items", "entire section",
]

def is_summarize_query(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in _SUMMARIZE_KEYWORDS)


# =====================================================
# DIRECT CHUNK LOADER (bypass hybrid search)
# =====================================================

def load_file_chunks_direct(user_id, filename, max_chunks: int = 0, section_hint: str = None, reverse_pages: bool = False) -> list:
    """
    Load chunks directly from a file without relevance filtering.
    max_chunks=0 means return all chunks.
    reverse_pages=True puts last pages first (useful for "latest" queries where
    new entries are appended at the end of the document).
    """
    upload_folder = f"uploads/user_{user_id}"
    if not os.path.exists(upload_folder):
        return []

    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path):
        return []

    try:
        docs = load_document(file_path)
        for doc in docs:
            if not doc.metadata.get("source"):
                doc.metadata["source"] = filename
    except Exception as e:
        print(f"Direct load failed for {filename}: {e}")
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    for c in chunks:
        if not c.metadata.get("source"):
            c.metadata["source"] = filename

    # Sort by page number for consistent ordering
    def _page(c):
        return c.metadata.get("page", 0)

    if reverse_pages:
        # Last pages first so LLM sees most recently appended content first
        chunks = sorted(chunks, key=_page, reverse=True)
    else:
        chunks = sorted(chunks, key=_page)

    print(f"DIRECT LOAD: {filename} → {len(chunks)} chunks (reverse={reverse_pages})")
    return chunks if max_chunks == 0 else chunks[:max_chunks]


# =====================================================
# DATE-AWARE ENTRY EXTRACTOR
# =====================================================

from datetime import datetime

_DATE_RE = re.compile(
    r'\b(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b'
)
_DATE_FMTS = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d']


def _parse_date_str(s: str):
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass
    return None


def build_sorted_entries_context(docs: list, section_hint: str = None, newest_first: bool = True) -> str:
    """
    Line-based dated-entry parser.
    A new entry starts whenever a line begins with a date token (M/D/YY or YYYY-MM-DD).
    Continuation lines (no leading date) are appended to the current entry.
    Entries are then sorted by date so the LLM just reads top-to-bottom.
    Falls back to raw text if no dated entries are found.
    """
    full_text = "\n\n".join(d.page_content for d in docs)

    # Narrow to section if hint given
    search_text = full_text
    if section_hint:
        idx = full_text.lower().find(section_hint.lower())
        if idx != -1:
            section_text = full_text[idx:]
            # Cut at the next all-uppercase section header
            nxt = re.search(r'\n[A-Z][A-Z &/\-]{3,}[:\n]', section_text[30:])
            if nxt:
                section_text = section_text[:30 + nxt.start()]
            search_text = section_text

    _ENTRY_START = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4})\b')

    entries: list[tuple] = []          # (datetime, [lines])
    current_date = None
    current_lines: list[str] = []

    for raw_line in search_text.splitlines():
        line = raw_line.strip()
        m = _ENTRY_START.match(line)
        if m:
            # Flush previous entry
            if current_date is not None and current_lines:
                entries.append((current_date, "\n".join(current_lines).strip()))
            date_obj = _parse_date_str(m.group(1))
            if date_obj:
                current_date = date_obj
                current_lines = [line]
            else:
                current_date = None
                current_lines = []
        else:
            if current_date is not None and line:
                current_lines.append(line)

    # Flush last entry
    if current_date is not None and current_lines:
        entries.append((current_date, "\n".join(current_lines).strip()))

    if not entries:
        print("DATE-SORT: no date-prefixed entries found, returning raw text")
        return full_text

    entries.sort(key=lambda x: x[0], reverse=newest_first)
    print(f"DATE-SORT: {len(entries)} entries, newest={entries[0][0].strftime('%m/%d/%Y')}")

    label = "ENTRIES (newest → oldest):" if newest_first else "ENTRIES (oldest → newest):"
    return label + "\n\n" + "\n\n---\n\n".join(text for _, text in entries)


# =====================================================
# DOCUMENT CLASSIFIER
# =====================================================


# =====================================================
# JSON OUTPUT DETECTION
# =====================================================

def wants_json_output(
    query
):

    json_keywords = [
        "json",
        "json format",
        "return json",
        "output json",
        "give json",
        "respond in json"
    ]

    query_lower = query.lower()

    return any(
        keyword in query_lower
        for keyword in json_keywords
    )

# =====================================================
# QUERY REWRITING
# =====================================================

def rewrite_query(
    query,
    chat_history
):

    if not chat_history:

        return query

    history_text = ""

    for message in chat_history[-4:]:

        history_text += (
            f"{message['role']}: "
            f"{message['content']}\n"
        )

    rewrite_prompt = f"""
You are a query rewriting assistant.

Rewrite the current question into a
clear standalone query using
conversation history.

Conversation:
{history_text}

Current Question:
{query}

Rewritten Question:
"""

    rewritten = llm.invoke(
        rewrite_prompt
    )

    return rewritten.content.strip()


# =====================================================
# DETECT FILE NAME IN QUERY
# =====================================================

def detect_filename(
    query,
    user_id
):

    upload_folder = (
        f"uploads/user_{user_id}"
    )

    if not os.path.exists(
        upload_folder
    ):

        return None

    uploaded_files = os.listdir(
        upload_folder
    )

    query_lower = query.lower()

    for file in uploaded_files:

        # exact filename match

        if file.lower() in query_lower:

            return file

        # filename without extension

        file_without_ext = (
            os.path.splitext(file)[0]
            .lower()
        )

        if file_without_ext in query_lower:

            return file

    return None

def detect_multiple_files(
    query,
    user_id
):

    upload_folder = (
        f"uploads/user_{user_id}"
    )

    if not os.path.exists(
        upload_folder
    ):

        return []

    uploaded_files = os.listdir(
        upload_folder
    )

    found_files = []

    query_lower = query.lower()

    for file in uploaded_files:

        file_lower = file.lower()

        file_without_ext = (
            os.path.splitext(file)[0]
            .lower()
        )

        if (
            file_lower in query_lower
            or
            file_without_ext in query_lower
        ):

            found_files.append(
                file
            )

    return found_files

# =====================================================
# FILTER DOCUMENTS BY FILE
# =====================================================

def filter_docs_by_filename(
    docs,
    filename
):

    filtered_docs = []

    for doc in docs:

        source = doc.metadata.get(
            "source",
            ""
        )

        if source == filename:

            filtered_docs.append(doc)

    return filtered_docs


def detect_image_file(
    query,
    user_id
):

    upload_folder = (
        f"uploads/user_{user_id}"
    )

    if not os.path.exists(
        upload_folder
    ):

        return None

    query_lower = query.lower()

    for file in os.listdir(
        upload_folder
    ):

        if not file.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):
            continue

        filename = os.path.splitext(
            file
        )[0].lower()

        if filename in query_lower:

            return file

    return None

# =====================================================
# ARRAY DIMENSIONS HELPER
# =====================================================

def _run_array_dimensions(user_id, selected_file):
    upload_folder = f"uploads/user_{user_id}"
    os.makedirs(upload_folder, exist_ok=True)

    if selected_file and selected_file.lower().endswith(".pdf"):
        pdf_path = os.path.join(upload_folder, selected_file)
    else:
        pdf_files = sorted(
            [
                os.path.join(upload_folder, f)
                for f in os.listdir(upload_folder)
                if f.lower().endswith(".pdf")
            ],
            key=os.path.getmtime,
            reverse=True
        )
        pdf_path = pdf_files[0] if pdf_files else None

    if not pdf_path or not os.path.exists(pdf_path):
        return {
            "prompt": "No PDF found. Please upload a CAD drawing PDF first.",
            "sources": [],
            "tool_used": "array_dimensions"
        }

    dims = extract_array_dimensions(pdf_path)
    filename = os.path.basename(pdf_path)

    lines = [f"## Array Dimensions — {filename}\n"]
    lines.append("| Page | Width | Height |")
    lines.append("|------|-------|--------|")

    for pg, info in dims.items():
        w = info["width"] or "—"
        h = info["height"] or "—"
        lines.append(f"| {pg} | {w} | {h} |")

    return {
        "prompt": "\n".join(lines),
        "sources": [],
        "tool_used": "array_dimensions"
    }


# =====================================================
# ASK QUESTION
# =====================================================

def ask_question(
    query,
    user_id,
    chat_history=None,
    selected_file=None,
    tracked_files=None
):

    # -------------------------------------------------
    # TOOL DETECTION
    # -------------------------------------------------

    tool = detect_tool(
        query
    )

    print(
        "DETECTED TOOL:",
        tool
    )

    if tool == "file_list":

        upload_folder = (
            f"uploads/user_{user_id}"
        )

        if not os.path.exists(
            upload_folder
        ):

            return {
                "prompt": (
                    "No documents uploaded."
                ),
                "sources": []
            }

        files = os.listdir(
            upload_folder
        )

        return {
            "prompt": (
                "Uploaded Documents:\n\n"
                + "\n".join(
                    [f"• {f}" for f in files]
                )
            ),
            "sources": [],
            "tool_used": "file_list"
        }

    if tool == "array_dimensions":
        return _run_array_dimensions(user_id, selected_file)

    json_mode = wants_json_output(
        query
    )   

    upload_folder = f"uploads/user_{user_id}"

    os.makedirs(upload_folder, exist_ok=True)

    pdf_files = sorted(
        [
            os.path.join(upload_folder, f)
            for f in os.listdir(upload_folder)
            if f.lower().endswith(".pdf")
        ],
        key=os.path.getmtime,
        reverse=True
    )

    if len(pdf_files) > 0:

        if selected_file:

            current_pdf = os.path.join(
                upload_folder,
                selected_file
            )

        else:

            current_pdf = pdf_files[0]

        print(
            "CLASSIFYING FILE:",
            current_pdf
        )

        print(
            "SELECTED FILE:",
            selected_file
        )

        if (
            tool is None
            and len(pdf_files) > 0
        ):

            if selected_file:

                current_pdf = os.path.join(
                    upload_folder,
                    selected_file
                )

            else:

                current_pdf = pdf_files[0]

            print(
                "ROUTING FILE:",
                current_pdf
            )

            tool = llm_route(
                query,
                current_pdf
            )

            # Extract tool from router decision
            if isinstance(tool, dict):
                tool = tool.get("tool")

            if tool == "array_dimensions":
                return _run_array_dimensions(user_id, selected_file)

            if tool == "rag_search":
                tool = None

    # -------------------------------------------------
    # CAD REVIEW TOOL
    # -------------------------------------------------
    if tool == "cad_review":

        print(
            "CAD REVIEW TOOL EXECUTING"
        )

        upload_folder = (
            f"uploads/user_{user_id}"
        )

        if not os.path.exists(
            upload_folder
        ):

            return {
                "prompt":
                    "No uploaded files found.",
                "sources": []
            }

        pdf_files = sorted(
            [
                os.path.join(
                    upload_folder,
                    f
                )
                for f in os.listdir(
                    upload_folder
                )
                if f.lower().endswith(
                    ".pdf"
                )
            ],
            key=os.path.getmtime,
            reverse=True
        )

        if len(pdf_files) == 0:

            return {
                "prompt":
                    "No PDF drawings found.",
                "sources": []
            }

        if selected_file:
            pdf_path = os.path.join(
                upload_folder,
                selected_file
            )
        else:
            pdf_path = pdf_files[0]

        report = cad_review_tool(
            pdf_path
        )

        formatted_report = (
            "🔍 CAD REVIEW REPORT\n\n"
        )

        for page in report:

            formatted_report += (
                f"Page {page['page']}\n"
            )

            formatted_report += (
                f"Status: {page['status']}\n"
            )

            if page["errors"]:

                formatted_report += (
                    "Errors:\n"
                )

                for error in page[
                    "errors"
                ]:

                    formatted_report += (
                        f"• {error}\n"
                    )

            formatted_report += "\n"

        return {
            "prompt": formatted_report,
            "sources": [
                os.path.basename(
                    pdf_path
                )
            ],
            "tool_used":
                "cad_review"
        }
    # -------------------------------------------------
    # CALCULATOR TOOL
    # -------------------------------------------------

    if tool == "calculator":

        result = calculator_tool(
            query
        )

        return {
            "prompt": (
                f"The calculated result is: "
                f"{result}"
            ),
            "sources": [],
            "tool_used": "calculator"
        }

    # -------------------------------------------------
    # WEB SEARCH TOOL
    # -------------------------------------------------

    if tool == "web_search":

        search_results = web_search_tool(
            query
        )

        web_prompt = f"""
You are an AI assistant.

Use the web search results below
to answer the user's question.

Web Results:
{search_results}

Question:
{query}

Answer:
"""

        web_response = llm.invoke(
            web_prompt
        )

        return {
            "prompt": web_response.content,
            "sources": ["Web Search"],
            "tool_used": "web_search"
        }

    # -------------------------------------------------
    # VISION TOOL
    # -------------------------------------------------

    if tool == "vision":

        upload_folder = (
            f"uploads/user_{user_id}"
        )

        image_files = []

        if os.path.exists(
            upload_folder
        ):

            for file in os.listdir(
                upload_folder
            ):

                if file.lower().endswith(
                    (
                        ".png",
                        ".jpg",
                        ".jpeg"
                    )
                ):

                    image_files.append(
                        file
                    )

        if len(image_files) == 0:

            return {
                "prompt": (
                    "No images uploaded."
                ),
                "sources": []
            }

        detected_image = detect_image_file(
            query,
            user_id
        )

        if detected_image:

            latest_image = detected_image

        else:

            latest_image = image_files[-1]

        image_path = os.path.join(
            upload_folder,
            latest_image
        )

        result = vision_tool(
            image_path,
            query
        )

        return {
            "prompt": result,
            "sources": [latest_image],
            "tool_used": "vision"
        }

    # -------------------------------------------------
    # QUERY REWRITE
    # -------------------------------------------------

    rewritten_query = rewrite_query(
        query,
        chat_history
    )

    # -------------------------------------------------
    # LOAD VECTOR STORE
    # -------------------------------------------------

    vector_store = load_user_vector_store(
        user_id
    )

    if vector_store is None:

        return {
            "prompt": (
                "No documents uploaded yet."
            ),
            "sources": []
        }

    # -------------------------------------------------
    # LOAD CHUNKS
    # -------------------------------------------------

    chunks = load_all_chunks(
        user_id
    )

    if len(chunks) == 0:

        return {
            "prompt": (
                "No document chunks found."
            ),
            "sources": []
        }

    # -------------------------------------------------
    # DETECT FILE-SPECIFIC QUERY
    # -------------------------------------------------

    detected_file = selected_file

    if not detected_file:

        detected_file = detect_filename(
            query,
            user_id
        )

    # -------------------------------------------------
    # SUMMARIZE FAST-PATH
    # For broad summarization queries, bypass hybrid search
    # and load chunks directly so nothing gets filtered out.
    # -------------------------------------------------

    detected_files = []
    _q_lower = query.lower()
    _latest_keywords = [
        "latest", "most recent", "newest", "last instruction",
        "recent instruction", "latest instruction", "latest information",
        "recent information", "recent entry",
    ]
    _list_all_keywords = [
        "all instruction", "all the instruction", "list all", "list the instruction",
        "give all", "all entries", "every instruction",
    ]
    is_latest_query = any(k in _q_lower for k in _latest_keywords)
    is_list_all_query = any(k in _q_lower for k in _list_all_keywords)

    _section_patterns = [
        "other information", "other instruction", "special instruction",
        "additional information", "additional instruction",
    ]
    section_hint = next((p for p in _section_patterns if p in _q_lower), None)

    if is_summarize_query(query) and detected_file:
        print(f"SUMMARIZE PATH: {detected_file} (latest={is_latest_query}, section={section_hint})")
        docs = load_file_chunks_direct(user_id, detected_file, max_chunks=0, reverse_pages=False)
    else:
        # -------------------------------------------------
        # CREATE BM25
        # -------------------------------------------------

        bm25 = create_bm25_retriever(
            chunks
        )

        # -------------------------------------------------
        # HYBRID SEARCH
        # -------------------------------------------------

        docs = hybrid_search(
            rewritten_query,
            vector_store,
            bm25,
            chunks,
            k=8
        )

        # -------------------------------------------------
        # MULTI FILE DETECTION
        # -------------------------------------------------

        detected_files = detect_multiple_files(
            query,
            user_id
        )

        # -------------------------------------------------
        # MULTI FILE FILTERING
        # -------------------------------------------------

        if len(detected_files) >= 2:

            filtered_docs = []

            for doc in docs:

                source = doc.metadata.get(
                    "source",
                    ""
                )

                if source in detected_files:

                    filtered_docs.append(
                        doc
                    )

            docs = filtered_docs

        # -------------------------------------------------
        # SINGLE FILE FILTERING
        # -------------------------------------------------

        elif detected_file:

            docs = filter_docs_by_filename(
                docs,
                detected_file
            )

        # -------------------------------------------------
        # RERANK
        # -------------------------------------------------

        docs = rerank_documents(
            rewritten_query,
            docs,
            top_k=6
        )

    # -------------------------------------------------
    # FALLBACK: if retrieval returned nothing,
    # load chunks directly from the target file
    # -------------------------------------------------

    if not docs:
        fallback_file = detected_file
        if not fallback_file:
            # pick the most recently uploaded file
            upload_folder = f"uploads/user_{user_id}"
            pdf_files = sorted(
                [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))],
                key=lambda f: os.path.getmtime(os.path.join(upload_folder, f)),
                reverse=True,
            )
            fallback_file = pdf_files[0] if pdf_files else None

        if fallback_file:
            print(f"FALLBACK: loading {fallback_file} directly (hybrid search returned nothing)")
            docs = load_file_chunks_direct(user_id, fallback_file, max_chunks=0)

    # -------------------------------------------------
    # BUILD CONTEXT
    # For "latest" or "list all" queries, pre-sort dated entries
    # in Python so the LLM doesn't have to compare dates itself.
    # -------------------------------------------------

    if (is_latest_query or is_list_all_query) and docs:
        context = build_sorted_entries_context(
            docs,
            section_hint=section_hint,
            newest_first=True,   # always newest-first; prompt tells LLM what to do
        )
        print(f"DATE-SORTED CONTEXT built (latest={is_latest_query}, list_all={is_list_all_query})")
    else:
        context = "\n\n".join(doc.page_content for doc in docs)

    # -------------------------------------------------
    # SOURCES
    # -------------------------------------------------

    sources = []

    for doc in docs:

        source = doc.metadata.get(
            "source",
            "Unknown"
        )

        page = (
            doc.metadata.get(
                "page",
                0
            ) + 1
        )

        source_text = (
            f"{source} (Page {page})"
        )

        if source_text not in sources:

            sources.append(
                source_text
            )

    # -------------------------------------------------
    # CONVERSATION MEMORY
    # -------------------------------------------------

    history_text = ""

    if chat_history:

        for message in chat_history[-6:]:

            role = message["role"]

            content = message["content"]

            history_text += (
                f"{role}: {content}\n"
            )

    # -------------------------------------------------
    # UPLOADED FILES LIST (DB-tracked only)
    # -------------------------------------------------

    all_uploaded = tracked_files if tracked_files else []

    uploaded_files_text = (
        "\n".join([f"• {f}" for f in all_uploaded])
        if all_uploaded
        else "None"
    )

    # -------------------------------------------------
    # COMPARISON MODE
    # -------------------------------------------------

    comparison_mode = (
        len(detected_files) >= 2
    )

    if comparison_mode:

        system_instruction = """
    You are an expert document comparison assistant.

    Compare the retrieved documents.

    Provide:

    1. Similarities
    2. Differences
    3. Missing Information
    4. Key Insights
    5. Recommendations

    Use only the retrieved context.
    """

    else:
        if is_latest_query:
            system_instruction = """
    You are an advanced AI assistant specializing in document analysis.

    The Retrieved Context below has already been sorted NEWEST ENTRY FIRST by the system.
    The FIRST dated entry in the context IS the most recent one.

    Your task: return the first (topmost) entry from the Retrieved Context.
    Format your response as:
      Date: <date>
      Instruction: <full instruction text>

    Include the complete instruction text — do not truncate it.
    Do NOT say "I couldn't retrieve content" — the context is provided.
    Do not mention or list any other entries.
    """
        elif is_list_all_query:
            system_instruction = """
    You are an advanced AI assistant specializing in document analysis.

    The Retrieved Context below contains dated entries sorted NEWEST FIRST.
    Return ALL entries you find, reversing the order so the response reads oldest → newest.
    Format each as: [DATE]: [instruction text]
    Do NOT say "I couldn't retrieve content" — the context is provided.
    """
        else:
            system_instruction = """
    You are an advanced AI assistant specializing in document analysis.

    Answer ONLY based on the retrieved document context provided below.
    Do NOT guess, invent, or infer content from filenames or prior knowledge.
    Only say "I couldn't retrieve enough content" if the Retrieved Context below is
    completely empty — never say it when context is present.
    Never fabricate document content.
    """
    # -------------------------------------------------
    # FINAL PROMPT
    # -------------------------------------------------
    if json_mode:

        output_instruction = """
    Return ONLY valid JSON.

    Do not use markdown.

    Do not add explanations.

    Return parsable JSON only.
    """

    else:

        output_instruction = """
    Return a natural human-readable answer.
    """

    prompt = f"""
    {system_instruction}

    {output_instruction}

Use:
1. conversation history
2. uploaded documents list
3. retrieved document context

to answer accurately.

Uploaded Documents:
{uploaded_files_text}

Retrieved Context:
{context}

Conversation History:
{history_text}

Current Question:
{query}

Answer:
"""

    return {
        "prompt": prompt,
        "retrieved_docs": len(docs),
        "sources": sources,
        "json_mode": json_mode,
        "retrieved_sources": sources,
        "rewritten_query": rewritten_query,
        "detected_file": detected_file,
        "detected_files": detected_files,
        "comparison_mode": comparison_mode
    }   