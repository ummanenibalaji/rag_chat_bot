import os
import re
from collections import defaultdict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

try:
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words('english'))
except Exception:
    STOPWORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'that', 'this', 'these', 'those', 'it', 'its', 'and', 'or', 'but',
        'not', 'no', 'nor', 'so', 'yet', 'what', 'which', 'who', 'how',
        'when', 'where', 'why', 'i', 'we', 'you', 'he', 'she', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'our',
    }


# =====================================================
# EMBEDDING MODEL (upgraded: bge-base > MiniLM-L6)
# =====================================================

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


# =====================================================
# RERANKER (upgraded: L-12 > L-6)
# =====================================================

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
    max_length=512,
)


# =====================================================
# TOKENIZER WITH STOPWORD REMOVAL
# =====================================================

def tokenize(text: str) -> list[str]:
    tokens = re.sub(r'[^a-z0-9\s]', ' ', text.lower()).split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# =====================================================
# SMART CHUNKING
# =====================================================

def split_documents(documents: list) -> list:
    """
    Two-pass chunking:
    1. Large parent chunks (1500 chars) for context.
    2. Small child chunks (400 chars) for precise retrieval.
    Child chunks carry parent_content in metadata for context expansion.
    """
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        separators=['\n\n', '\n', '. ', '! ', '? ', ' ', ''],
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=['\n\n', '\n', '. ', '! ', '? ', ' ', ''],
    )

    child_chunks = []
    parent_chunks = parent_splitter.split_documents(documents)

    for parent in parent_chunks:
        children = child_splitter.split_documents([parent])
        for child in children:
            child.metadata['parent_content'] = parent.page_content
        child_chunks.extend(children)

    print(f"Chunking: {len(documents)} docs → {len(parent_chunks)} parents → {len(child_chunks)} children")
    return child_chunks


# =====================================================
# BM25 RETRIEVER
# =====================================================

def create_bm25_retriever(chunks: list) -> BM25Okapi:
    tokenized = [tokenize(c.page_content) for c in chunks]
    # Avoid empty corpus
    tokenized = [t if t else ['_empty_'] for t in tokenized]
    return BM25Okapi(tokenized)


# =====================================================
# RECIPROCAL RANK FUSION
# =====================================================

def reciprocal_rank_fusion(ranked_lists: list[list], k: int = 60) -> list:
    """
    Fuse multiple ranked document lists via RRF.
    Score = Σ 1/(k + rank) across all lists.
    """
    scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, Document] = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list):
            key = doc.page_content[:120]
            scores[key] += 1.0 / (k + rank + 1)
            doc_map[key] = doc

    fused = sorted(doc_map.values(), key=lambda d: scores[d.page_content[:120]], reverse=True)
    return fused


# =====================================================
# QUERY EXPANSION
# =====================================================

def expand_query(query: str) -> str:
    """
    Lightweight query expansion:
    - Append key noun phrases extracted by regex
    - Add domain synonyms for common terms
    """
    synonyms = {
        'summarize': 'summary overview',
        'explain': 'description explanation',
        'find': 'locate identify',
        'compare': 'comparison difference similarity',
        'error': 'issue problem fault',
        'table': 'data structured grid',
        'date': 'time period when',
        'cost': 'price amount fee',
        'invoice': 'bill statement receipt',
        'total': 'sum aggregate overall',
    }
    expanded = query
    for word, expansion in synonyms.items():
        if word in query.lower() and expansion not in expanded.lower():
            expanded += f' {expansion}'
    return expanded


# =====================================================
# HYBRID SEARCH WITH RRF
# =====================================================

def hybrid_search(
    query: str,
    vector_store,
    bm25: BM25Okapi,
    chunks: list,
    k: int = 8,
) -> list:

    expanded_query = expand_query(query)

    # 1. Semantic search (MMR for diversity)
    try:
        semantic_docs = vector_store.max_marginal_relevance_search(
            expanded_query, k=k * 2, fetch_k=k * 4, lambda_mult=0.6
        )
    except Exception:
        semantic_docs = vector_store.similarity_search(expanded_query, k=k * 2)

    # 2. BM25 keyword search
    tokenized_query = tokenize(expanded_query)
    if not tokenized_query:
        tokenized_query = ['_empty_']
    bm25_scores = bm25.get_scores(tokenized_query)
    top_bm25_idx = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:k * 2]
    keyword_docs = [chunks[i] for i in top_bm25_idx]

    # 3. RRF fusion
    fused = reciprocal_rank_fusion([semantic_docs, keyword_docs], k=60)

    # 4. Metadata-based filename prioritization
    query_lower = query.lower()
    priority, rest = [], []
    for doc in fused:
        src = doc.metadata.get('source', '').lower()
        if src and src in query_lower:
            priority.append(doc)
        else:
            rest.append(doc)
    fused = priority + rest

    # 5. Deduplicate
    seen, unique = set(), []
    for doc in fused:
        key = doc.page_content[:100]
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    return unique[:k * 2]


# =====================================================
# RERANK WITH PARENT CONTEXT EXPANSION
# =====================================================

def rerank_documents(
    query: str,
    docs: list,
    top_k: int = 6,
    score_threshold: float = -10.0,
    max_chunks_per_source: int = 4,
) -> list:

    if not docs:
        return []

    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)

    scored = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

    results, seen_sources = [], defaultdict(int)
    for doc, score in scored:
        if score < score_threshold:
            continue
        src = doc.metadata.get('source', 'unknown')
        if seen_sources[src] < max_chunks_per_source:
            parent = doc.metadata.get('parent_content')
            if parent and len(parent) > len(doc.page_content):
                expanded = Document(page_content=parent, metadata=doc.metadata)
                results.append(expanded)
            else:
                results.append(doc)
            seen_sources[src] += 1
        if len(results) >= top_k:
            break

    print(f"\nReranked: {len(results)} docs returned (threshold={score_threshold})")
    for d in results:
        print(f"  source={d.metadata.get('source')} score_pass=True")

    return results


# =====================================================
# VECTOR STORE OPERATIONS
# =====================================================

def create_vector_store(chunks: list):
    return FAISS.from_documents(chunks, embeddings)


def save_vector_store(vector_store, save_path: str):
    os.makedirs(save_path, exist_ok=True)
    vector_store.save_local(save_path)


def load_vector_store(load_path: str):
    return FAISS.load_local(
        load_path, embeddings, allow_dangerous_deserialization=True
    )


# =====================================================
# PROCESS DOCUMENTS
# =====================================================

def process_documents(documents: list, save_path: str = None) -> dict:
    chunks = split_documents(documents)
    vector_store = create_vector_store(chunks)

    if save_path:
        save_vector_store(vector_store, save_path)

    bm25 = create_bm25_retriever(chunks)

    return {
        'chunks': chunks,
        'vector_store': vector_store,
        'bm25': bm25,
    }


# =====================================================
# LOAD PDF DOCUMENTS
# =====================================================

def load_documents(file_paths: list) -> list:
    documents = []
    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata['source'] = os.path.basename(file_path)
        documents.extend(docs)
    return documents


# =====================================================
# RETRIEVE RELEVANT DOCUMENTS
# =====================================================

def retrieve_documents(query: str, vector_store, bm25, chunks, k: int = 5) -> list:
    return hybrid_search(query, vector_store, bm25, chunks, k)
