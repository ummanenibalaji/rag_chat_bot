import os

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from sentence_transformers import (
    CrossEncoder
)

from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_community.vectorstores import (
    FAISS
)

from langchain_huggingface import (
    HuggingFaceEmbeddings
)

from rank_bm25 import BM25Okapi


# =====================================================
# EMBEDDING MODEL
# =====================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# =====================================================
# RERANKER MODEL
# =====================================================

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# =====================================================
# LOAD PDF DOCUMENTS
# =====================================================

def load_documents(
    file_paths
):

    documents = []

    for file_path in file_paths:

        loader = PyPDFLoader(
            file_path
        )

        docs = loader.load()

        for doc in docs:

            doc.metadata["source"] = (
                os.path.basename(file_path)
            )

        documents.extend(docs)

    return documents


# =====================================================
# SPLIT DOCUMENTS INTO CHUNKS
# =====================================================

def split_documents(
    documents
):

    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    )

    chunks = text_splitter.split_documents(
        documents
    )

    return chunks


# =====================================================
# BM25 KEYWORD RETRIEVAL
# =====================================================

def create_bm25_retriever(
    chunks
):

    tokenized_chunks = [
        chunk.page_content.lower().split()
        for chunk in chunks
    ]

    bm25 = BM25Okapi(
        tokenized_chunks
    )

    return bm25


# =====================================================
# HYBRID SEARCH
# =====================================================

def hybrid_search(
    query,
    vector_store,
    bm25,
    chunks,
    k=4
):

    # -------------------------------------------------
    # SEMANTIC SEARCH
    # -------------------------------------------------

    semantic_docs = vector_store.similarity_search(
        query,
        k=12    
    )

    # -------------------------------------------------
    # BM25 KEYWORD SEARCH
    # -------------------------------------------------

    tokenized_query = query.lower().split()

    bm25_scores = bm25.get_scores(
        tokenized_query
    )

    top_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True
    )[:12]

    keyword_docs = [
        chunks[i]
        for i in top_indices
    ]

    # -------------------------------------------------
    # MERGE RESULTS
    # -------------------------------------------------

    combined_docs = semantic_docs + keyword_docs
    # -------------------------------------------------
# METADATA PRIORITIZATION
# -------------------------------------------------

    query_lower = query.lower()

    prioritized_docs = []

    for doc in combined_docs:

        source = (
            doc.metadata.get(
                "source",
                ""
            ).lower()
        )

        if source and source in query_lower:

            prioritized_docs.insert(
                0,
                doc
            )

        else:

            prioritized_docs.append(
                doc
            )

    combined_docs = prioritized_docs

    unique_docs = []

    seen = set()

    for doc in combined_docs:

        content = doc.page_content

        if content not in seen:

            seen.add(content)

            unique_docs.append(doc)

    return unique_docs[:12]

# =====================================================
# RERANK DOCUMENTS
# =====================================================

def rerank_documents(
    query,
    docs,
    top_k=4
):

    if len(docs) == 0:

        return []

    pairs = [
        (
            query,
            doc.page_content
        )
        for doc in docs
    ]

    scores = reranker.predict(
        pairs
    )

    scored_docs = list(
        zip(docs, scores)
    )

    scored_docs.sort(
        key=lambda x: x[1],
        reverse=True
    )

    reranked_docs = []

    seen_sources = {}

    for doc, score in scored_docs:

        source = doc.metadata.get(
            "source",
            "unknown"
        )

        count = seen_sources.get(
            source,
            0
        )

        if count < 2:

            reranked_docs.append(
                doc
            )

            seen_sources[source] = (
                count + 1
            )

        if len(reranked_docs) >= top_k:

            break
    print("\nRERANKED SOURCES") 
    for doc in reranked_docs:

        print(
            doc.metadata.get(
                "source"
            )
        )
    return reranked_docs

# =====================================================
# CREATE VECTOR STORE
# =====================================================

def create_vector_store(
    chunks
):

    vector_store = FAISS.from_documents(
        chunks,
        embeddings
    )

    return vector_store


# =====================================================
# SAVE VECTOR STORE
# =====================================================

def save_vector_store(
    vector_store,
    save_path
):

    os.makedirs(
        save_path,
        exist_ok=True
    )

    vector_store.save_local(
        save_path
    )


# =====================================================
# LOAD VECTOR STORE
# =====================================================

def load_vector_store(
    load_path
):

    vector_store = FAISS.load_local(
        load_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


# =====================================================
# PROCESS DOCUMENTS
# =====================================================

def process_documents(
    documents,
    save_path=None
):

    # -------------------------------------------------
    # SPLIT DOCUMENTS
    # -------------------------------------------------

    chunks = split_documents(
        documents
    )

    # -------------------------------------------------
    # CREATE VECTOR STORE
    # -------------------------------------------------

    vector_store = create_vector_store(
        chunks
    )

    # -------------------------------------------------
    # SAVE VECTOR STORE
    # -------------------------------------------------

    if save_path:

        save_vector_store(
            vector_store,
            save_path
        )

    # -------------------------------------------------
    # CREATE BM25 RETRIEVER
    # -------------------------------------------------

    bm25 = create_bm25_retriever(
        chunks
    )

    return {
        "chunks": chunks,
        "vector_store": vector_store,
        "bm25": bm25
    }


# =====================================================
# GET RETRIEVER
# =====================================================

def get_retriever(
    vector_store
):

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 4}
    )

    return retriever


# =====================================================
# RETRIEVE RELEVANT DOCUMENTS
# =====================================================

def retrieve_documents(
    query,
    vector_store,
    bm25,
    chunks,
    k=4
):

    docs = hybrid_search(
        query,
        vector_store,
        bm25,
        chunks,
        k
    )

    return docs