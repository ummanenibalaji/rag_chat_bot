import os

from langchain_community.vectorstores import (
    FAISS
)

from embeddings import (
    get_embedding_model
)


# =====================================================
# GET USER FAISS PATH
# =====================================================

def get_faiss_path(
    user_id
):

    return (
        f"faiss_indexes/user_{user_id}"
    )


# =====================================================
# CREATE OR LOAD VECTOR STORE
# =====================================================

def create_or_load_vector_store(
    chunks,
    user_id
):

    embeddings = (
        get_embedding_model()
    )

    faiss_path = get_faiss_path(
        user_id
    )

    os.makedirs(
        os.path.dirname(
            faiss_path
        ),
        exist_ok=True
    )

    # -----------------------------------------
    # EXISTING INDEX
    # -----------------------------------------

    if os.path.exists(
        faiss_path
    ):

        vector_store = (
            FAISS.load_local(
                faiss_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
        )

        vector_store.add_documents(
            chunks
        )

    # -----------------------------------------
    # NEW INDEX
    # -----------------------------------------

    else:

        vector_store = (
            FAISS.from_documents(
                chunks,
                embeddings
            )
        )

    vector_store.save_local(
        faiss_path
    )

    return vector_store


# =====================================================
# LOAD VECTOR STORE
# =====================================================

def load_vector_store(
    user_id
):

    embeddings = (
        get_embedding_model()
    )

    faiss_path = get_faiss_path(
        user_id
    )

    if not os.path.exists(
        faiss_path
    ):

        return None

    vector_store = (
        FAISS.load_local(
            faiss_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    )

    return vector_store