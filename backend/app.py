import os

# Load .env before any HuggingFace imports to prevent online version-check hangs
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Body,
    Header
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    StreamingResponse
)

import chatbot

from llm_providers import answer_llm, llm_status, list_ollama_models, swap_answer_model
import llm_providers

from email_utils import (
    send_reset_email
)

from document_loader import (
    load_document
)

from rag_pipeline import (
    process_documents
)

from chatbot import (
    ask_question
)

from database import (
    engine,
    SessionLocal
)

from models import (
    Base,
    UploadedFile,
    User,
    Conversation,
    Message
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_reset_token
)

from cad_checker import (
    extract_array_dimensions
)


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(
    bind=engine
)

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    "faiss_indexes",
    exist_ok=True
)


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():

    return {
        "message": (
            "RAG Chatbot Backend Running"
        )
    }


# =====================================================
# LLM STATUS
# =====================================================

@app.get("/llm-status")
def get_llm_status():
    return llm_status()


# =====================================================
# LIST OLLAMA MODELS
# =====================================================

@app.get("/ollama-models")
def get_ollama_models():
    return {
        "models": list_ollama_models(),
        "current": llm_providers._state["answer_model"],
    }


# =====================================================
# SWITCH ANSWER MODEL
# =====================================================

@app.post("/switch-model")
def switch_model(data: dict = Body(...), token: str = Header(...)):
    decode_access_token(token)  # auth check
    model_name = data.get("model")
    if not model_name:
        return {"error": "model field required"}
    result = swap_answer_model(model_name)
    # refresh the module-level reference app.py uses
    import llm_providers as _lp
    global answer_llm
    answer_llm = _lp.answer_llm
    return result


# =====================================================
# SIGNUP
# =====================================================

@app.post("/signup")
def signup(data: dict):

    email = data.get("email")

    password = data.get("password")

    db = SessionLocal()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:

        db.close()

        return {
            "message": (
                "User already exists"
            )
        }

    hashed_password = hash_password(
        password
    )

    new_user = User(
        email=email,
        hashed_password=hashed_password
    )

    db.add(new_user)

    db.commit()

    db.close()

    return {
        "message": (
            "User created successfully"
        )
    }


# =====================================================
# LOGIN
# =====================================================

@app.post("/login")
def login(data: dict):

    email = data.get("email")

    password = data.get("password")

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:

        db.close()

        return {
            "message": (
                "Invalid credentials"
            )
        }

    valid_password = verify_password(
        password,
        user.hashed_password
    )

    if not valid_password:

        db.close()

        return {
            "message": (
                "Invalid credentials"
            )
        }

    token = create_access_token(
        {"sub": user.email}
    )

    db.close()

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =====================================================
# FORGOT PASSWORD
# =====================================================

@app.post("/forgot-password")
def forgot_password(data: dict):

    email = data.get("email")

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:

        db.close()

        return {
            "message": "User not found"
        }

    reset_token = create_reset_token(
        email
    )

    email_sent = send_reset_email(
        email,
        reset_token
    )

    db.close()

    if email_sent:

        return {
            "message": (
                "Password reset email sent"
            )
        }

    return {
        "message": (
            "Failed to send email"
        )
    }


# =====================================================
# RESET PASSWORD
# =====================================================

@app.post("/reset-password")
def reset_password(data: dict):

    token = data.get("token")

    new_password = data.get(
        "new_password"
    )

    try:

        email = decode_access_token(
            token
        )

    except:

        return {
            "message": (
                "Invalid or expired token"
            )
        }

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:

        db.close()

        return {
            "message": "User not found"
        }

    user.hashed_password = hash_password(
        new_password
    )

    db.commit()

    db.close()

    return {
        "message": (
            "Password reset successful"
        )
    }


# =====================================================
# VALIDATE TOKEN
# =====================================================

@app.get("/validate-token")
def validate_token(
    token: str = Header(...)
):

    try:

        email = decode_access_token(
            token
        )

        db = SessionLocal()

        user = db.query(User).filter(
            User.email == email
        ).first()

        db.close()

        if not user:

            return {
                "valid": False
            }

        return {
            "valid": True,
            "email": user.email
        }

    except:

        return {
            "valid": False
        }


# =====================================================
# UPLOAD DOCUMENT
# =====================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(token)

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:

        db.close()

        return {
            "message": "Unauthorized or user not found."
        }

    # -------------------------------------------------
    # USER UPLOAD FOLDER
    # -------------------------------------------------

    user_upload_folder = os.path.join(
        UPLOAD_FOLDER,
        f"user_{user.id}"
    )

    os.makedirs(
        user_upload_folder,
        exist_ok=True
    )

    # -------------------------------------------------
    # VALIDATE FILE TYPE
    # -------------------------------------------------

    allowed_extensions = [
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".docx",
        ".txt",
        ".csv",
        ".xlsx",
        ".pptx"
    ]

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:

        return {
            "message": (
                "Unsupported file type"
            )
        }

    # -------------------------------------------------
    # SAVE FILE
    # -------------------------------------------------

    file_path = os.path.join(
        user_upload_folder,
        file.filename
    )

    with open(file_path, "wb") as f:

        f.write(await file.read())

    # -------------------------------------------------
    # LOAD DOCUMENT
    # -------------------------------------------------

    documents = load_document(
        file_path
    )

    # -------------------------------------------------
    # VECTOR STORE PATH
    # -------------------------------------------------

    save_path = (
        f"faiss_indexes/user_{user.id}"
    )

    # -------------------------------------------------
    # PROCESS DOCUMENTS
    # -------------------------------------------------

    result = process_documents(
        documents,
        save_path
    )

    # -------------------------------------------------
    # SAVE FILE RECORD
    # -------------------------------------------------

    existing_file = db.query(
        UploadedFile
    ).filter(
        UploadedFile.filename == file.filename,
        UploadedFile.user_id == user.id
    ).first()

    if not existing_file:

        db_file = UploadedFile(
            filename=file.filename,
            user_id=user.id
        )

        db.add(db_file)

        db.commit()

    db.close()

    return {
        "filename": file.filename,
        "pages": len(documents),
        "chunks_created": len(
            result["chunks"]
        ),
        "vector_store_created": True
    }


# =====================================================
# GET USER FILES
# =====================================================

@app.get("/files")
def get_uploaded_files(
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(
        token
    )

    user = db.query(User).filter(
        User.email == email
    ).first()

    files = db.query(
        UploadedFile
    ).filter(
        UploadedFile.user_id == user.id
    ).all()

    db.close()

    return [
        {
            "filename": file.filename
        }
        for file in files
    ]


# =====================================================
# ASK QUESTION
# =====================================================

@app.post("/ask")
async def ask(
    data: dict = Body(...),
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(token)

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        db.close()
        return {
            "message": "Unauthorized or user not found."
        }

    query = data.get("query")
    selected_file = data.get(
        "selected_file"
    )

    chat_history = data.get(
        "chat_history",
        []
    )

    conversation_id = data.get(
        "conversation_id"
    )

    # -------------------------------------------------
    # CREATE CONVERSATION
    # -------------------------------------------------

    if not conversation_id:

        conversation = Conversation(
            user_id=user.id,
            title=query[:30]
        )

        db.add(conversation)

        db.commit()

        db.refresh(conversation)

        conversation_id = (
            conversation.id
        )

    # -------------------------------------------------
    # STORE USER MESSAGE
    # -------------------------------------------------

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=query
    )

    db.add(user_message)

    db.commit()

    # -------------------------------------------------
    # ASK QUESTION
    # -------------------------------------------------

    db_files = db.query(UploadedFile).filter(
        UploadedFile.user_id == user.id
    ).all()
    tracked_files = [f.filename for f in db_files]

    response = ask_question(
        query=query,
        user_id=user.id,
        chat_history=chat_history,
        selected_file=selected_file,
        tracked_files=tracked_files
    )

    prompt = response["prompt"]

    if response.get("tool_used") in (
        "cad_review", "array_dimensions", "file_list"
    ):
        return StreamingResponse(
            iter([prompt]),
            media_type="text/plain",
            headers={
                "conversation_id": str(
                    conversation_id
                )
            }
        )

    sources = response.get(
        "sources",
        []
    )

    full_response = ""

    stream = llm_providers.answer_llm.stream(
        prompt
    )

    def generate():

        nonlocal full_response

        for chunk in stream:

            token_chunk = chunk.content

            full_response += token_chunk

            yield token_chunk

        # ---------------------------------------------
        # APPEND SOURCES
        # ---------------------------------------------

        if len(sources) > 0:

            sources_text = (
                "\n\n📚 Sources:\n"
            )

            for source in sources:

                sources_text += (
                    f"- {source}\n"
                )

            full_response += (
                sources_text
            )

            yield sources_text

        # ---------------------------------------------
        # STORE ASSISTANT MESSAGE
        # ---------------------------------------------

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response
        )

        db.add(assistant_message)

        db.commit()

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "conversation_id": str(
                conversation_id
            )
        }
    )


# =====================================================
# DELETE FILE
# =====================================================

@app.delete("/delete-file")
def delete_file(
    filename: str,
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(
        token
    )

    user = db.query(User).filter(
        User.email == email
    ).first()

    file = db.query(
        UploadedFile
    ).filter(
        UploadedFile.filename == filename,
        UploadedFile.user_id == user.id
    ).first()

    if not file:

        db.close()

        return {
            "message": "File not found"
        }

    # -------------------------------------------------
    # DELETE PHYSICAL FILE
    # -------------------------------------------------

    user_upload_folder = os.path.join(
        UPLOAD_FOLDER,
        f"user_{user.id}"
    )

    file_path = os.path.join(
        user_upload_folder,
        filename
    )

    if os.path.exists(file_path):

        os.remove(file_path)

    # -------------------------------------------------
    # DELETE DATABASE RECORD
    # -------------------------------------------------

    db.delete(file)

    db.commit()

    db.close()

    return {
        "message": (
            f"{filename} deleted successfully"
        )
    }


# =====================================================
# CREATE CONVERSATION
# =====================================================

@app.post("/create-conversation")
def create_conversation(
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(
        token
    )

    user = db.query(User).filter(
        User.email == email
    ).first()

    conversation = Conversation(
        user_id=user.id,
        title="New Chat"
    )

    db.add(conversation)

    db.commit()

    db.refresh(conversation)

    db.close()

    return {
        "conversation_id": conversation.id
    }


# =====================================================
# GET CONVERSATIONS
# =====================================================

@app.get("/conversations")
def get_conversations(
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(
        token
    )

    user = db.query(User).filter(
        User.email == email
    ).first()

    conversations = db.query(
        Conversation
    ).filter(
        Conversation.user_id == user.id
    ).order_by(
        Conversation.created_at.desc()
    ).all()

    result = []

    for conversation in conversations:

        result.append(
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": str(
                    conversation.created_at
                )
            }
        )

    db.close()

    return result


# =====================================================
# GET MESSAGES
# =====================================================

@app.get("/messages/{conversation_id}")
def get_messages(
    conversation_id: int,
    token: str = Header(...)
):

    db = SessionLocal()

    messages = db.query(
        Message
    ).filter(
        Message.conversation_id == conversation_id
    ).all()

    result = []

    for message in messages:

        result.append(
            {
                "role": message.role,
                "content": message.content
            }
        )

    db.close()

    return result

# =====================================================
# DELETE CONVERSATION
# =====================================================

@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    token: str = Header(...)
):
    db = SessionLocal()

    email = decode_access_token(token)
    user = db.query(User).filter(User.email == email).first()

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()

    if not conversation:
        db.close()
        return {"message": "Not found"}

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conversation)
    db.commit()
    db.close()

    return {"message": "Deleted"}


@app.get("/documents")
async def get_documents(
    token: str = Header(...)
):

    db = SessionLocal()

    email = decode_access_token(token)

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        db.close()
        return {
            "documents": []
        }

    upload_folder = os.path.join(
        "uploads",
        f"user_{user.id}"
    )

    if not os.path.exists(upload_folder):
        db.close()
        return {
            "documents": []
        }

    files = []

    for f in os.listdir(upload_folder):
        if os.path.isfile(
            os.path.join(upload_folder, f)
        ):
            files.append(f)

    db.close()

    return [{"filename": f} for f in files]


# =====================================================
# ARRAY DIMENSIONS
# =====================================================

@app.get("/array-dimensions")
async def get_array_dimensions(
    filename: str,
    token: str = Header(None)
):
    user_id = decode_access_token(token)

    if not user_id:
        return {"error": "Unauthorized"}

    file_path = os.path.join(
        "uploads",
        f"user_{user_id}",
        filename
    )

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    if not filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files supported"}

    dims = extract_array_dimensions(file_path)

    return {
        "filename": filename,
        "pages": dims
    }