import os
import re

from document_loader import (
    load_document
)

from langchain_community.vectorstores import (
    FAISS
)

from langchain_huggingface import (
    HuggingFaceEmbeddings
)

from langchain_ollama import (
    ChatOllama
)

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
    vision_tool
)


# =====================================================
# LLM
# =====================================================

llm = ChatOllama(
    model="llama3"
)


# =====================================================
# LOAD USER VECTOR STORE
# =====================================================

def load_user_vector_store(
    user_id
):

    embeddings = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )

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
# =====================================================

def detect_tool(
    query
):

    math_keywords = [
        "+",
        "-",
        "*",
        "/",
        "%",
        "calculate",
        "sqrt",
        "square root"
    ]

    web_keywords = [
        "today",
        "latest",
        "current",
        "news",
        "stock price",
        "market",
        "internet",
        "online"
    ]

    vision_keywords = [
        "image",
        "photo",
        "screenshot",
        "picture",
        "diagram",
        "chart",
        "graph",
        "analyze image",
        "what does this image contain"
    ]

    query_lower = query.lower()

    # -------------------------------------------------
    # CALCULATOR
    # -------------------------------------------------

    for keyword in math_keywords:

        if keyword in query_lower:

            return "calculator"

    # -------------------------------------------------
    # WEB SEARCH
    # -------------------------------------------------

    for keyword in web_keywords:

        if keyword in query_lower:

            return "web_search"

    # -------------------------------------------------
    # VISION TOOL
    # -------------------------------------------------

    for keyword in vision_keywords:

        if keyword in query_lower:

            return "vision"

    return None

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


# =====================================================
# ASK QUESTION
# =====================================================

def ask_question(
    query,
    user_id,
    chat_history=None,
    selected_file=None
):

    # -------------------------------------------------
    # TOOL DETECTION
    # -------------------------------------------------

    tool = detect_tool(
        query
    )

    json_mode = wants_json_output(
        query
    )

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
        top_k=4
    )

    # -------------------------------------------------
    # BUILD CONTEXT
    # -------------------------------------------------

    context = "\n\n".join(
        [
            doc.page_content
            for doc in docs
        ]
    )

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

        system_instruction = """
    You are an advanced AI assistant.

    Use only the provided context.

    If information is unavailable,
    say so.
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
2. retrieved document contextff

to answer accurately.   

Only use the provided context.

If answer is unavailable,
say:

'I could not find that information in the document.'

Conversation History:
{history_text}

Retrieved Context:
{context}

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