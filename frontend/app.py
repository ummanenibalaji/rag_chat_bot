import os
import json
import streamlit as st
import requests

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from io import BytesIO

def generate_pdf_report(
    question,
    answer
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = (
        getSampleStyleSheet()
    )

    elements = []

    elements.append(
        Paragraph(
            "AI Document Assistant Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            f"<b>Question:</b><br/>{question}",
            styles["BodyText"]
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            f"<b>Answer:</b><br/>{answer}",
            styles["BodyText"]
        )
    )

    doc.build(
        elements
    )

    pdf = buffer.getvalue()

    buffer.close()

    return pdf
def generate_conversation_pdf(
    messages
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = (
        getSampleStyleSheet()
    )

    elements = []

    elements.append(
        Paragraph(
            "Conversation Export",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    for message in messages:

        role = message.get(
            "role",
            "Unknown"
        )

        content = message.get(
            "content",
            ""
        )

        elements.append(
            Paragraph(
                f"<b>{role.upper()}</b>",
                styles["Heading3"]
            )
        )

        elements.append(
            Paragraph(
                content,
                styles["BodyText"]
            )
        )

        elements.append(
            Spacer(1, 8)
        )

    doc.build(
        elements
    )

    pdf = buffer.getvalue()

    buffer.close()

    return pdf
# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Document Chatbot",
    page_icon="📄",
    layout="wide"
)

BACKEND_URL = "http://127.0.0.1:8000"

TOKEN_FILE = "token.txt"


# =====================================================
# SESSION STATE
# =====================================================

if "token" not in st.session_state:

    if os.path.exists(TOKEN_FILE):

        with open(TOKEN_FILE, "r") as f:

            st.session_state.token = f.read()

    else:

        st.session_state.token = None

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "messages" not in st.session_state:

    st.session_state.messages = []

if "conversation_id" not in st.session_state:

    st.session_state.conversation_id = None

if "uploader_key" not in st.session_state:

    st.session_state.uploader_key = 0

if "email" not in st.session_state:

    st.session_state.email = ""

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #0F172A 0%,
        #111827 100%
    );
}

.block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

[data-testid="stSidebar"] {
    background: #0B1220;
    border-right: 1px solid #1E293B;
}

h1,h2,h3 {
    color: white !important;
}

.stChatMessage {
    border-radius: 18px;
    padding: 12px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# TOKEN VALIDATION
# =====================================================

if st.session_state.token:

    try:

        response = requests.get(
            f"{BACKEND_URL}/validate-token",
            headers={
                "token": st.session_state.token
            }
        )

        data = response.json()

        if data.get("valid"):

            st.session_state.logged_in = True

            st.session_state.email = (
                data.get("email")
            )

        else:

            st.session_state.logged_in = False

            st.session_state.token = None

    except:

        st.error(
            "Backend server not running."
        )


# =====================================================
# LOGIN PAGE
# =====================================================

if not st.session_state.logged_in:

    st.markdown("""
    # 🤖 AI Document Assistant

    ### Enterprise RAG Platform
    Upload documents, analyze data, compare files and chat with your knowledge base.
    """)

    tab1, tab2 = st.tabs(
        [
            "Login",
            "Signup"
        ]
    )

    # =================================================
    # LOGIN
    # =================================================

    with tab1:

        email = st.text_input(
            "Email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            response = requests.post(
                f"{BACKEND_URL}/login",
                json={
                    "email": email,
                    "password": password
                }
            )

            st.write("Status:", response.status_code)
            st.write("Response:", response.text)

            try:

                data = response.json()

            except Exception:

                st.error(
                    f"Invalid backend response:\n{response.text}"
                )

                st.stop()

            if "access_token" in data:

                st.session_state.token = (
                    data["access_token"]
                )

                with open(TOKEN_FILE, "w") as f:

                    f.write(
                        data["access_token"]
                    )

                st.session_state.logged_in = True

                st.rerun()

            else:

                st.error(
                    data.get(
                        "message",
                        "Login failed"
                    )
                )

    # =================================================
    # SIGNUP
    # =================================================

    with tab2:

        new_email = st.text_input(
            "New Email"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        if st.button("Signup"):

            response = requests.post(
                f"{BACKEND_URL}/signup",
                json={
                    "email": new_email,
                    "password": new_password
                }
            )

            st.success(
                response.json().get(
                    "message"
                )
            )

    st.stop()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown("""
    # 🤖 AI Assistant

    ---
    """)
    st.success(
        f"Logged in as:\n"
        f"{st.session_state.email}"
    )

    # =================================================
    # LOGOUT
    # =================================================

    if st.button("Logout"):

        st.session_state.token = None
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.session_state.conversation_id = None

        if os.path.exists(TOKEN_FILE):

            os.remove(TOKEN_FILE)

        st.rerun()

    st.divider()

    # =================================================
    # NEW CHAT
    # =================================================

    if st.button("➕ New Chat"):

        st.session_state.messages = []

        st.session_state.conversation_id = None

        st.rerun()
    if len(
        st.session_state.messages
    ) > 0:

        conversation_pdf = (
            generate_conversation_pdf(
                st.session_state.messages
            )
        )

        st.download_button(
            label="📥 Export Conversation",
            data=conversation_pdf,
            file_name="conversation.pdf",
            mime="application/pdf"
    )
    # =================================================
    # CONVERSATIONS
    # =================================================

    st.subheader(
        "Conversations"
    )

    response = requests.get(
        f"{BACKEND_URL}/conversations",
        headers={
            "token": st.session_state.token
        }
    )
    documents_response = requests.get(
        f"{BACKEND_URL}/documents",
        headers={
            "token": st.session_state.token
        }
    )

    documents = []

    if documents_response.status_code == 200:

        documents = [
            doc["filename"]
            for doc in documents_response.json()
        ]
    selected_file = st.selectbox(
        "Search Scope",
        ["All Files"] + documents
    )
    st.session_state.selected_file = (
        None
        if selected_file == "All Files"
        else selected_file
    )
    if response.status_code == 200:

        conversations = response.json()

        if len(conversations) == 0:

            st.info(
                "No conversations yet."
            )

        for conv in conversations:

            if st.button(
                f"💬 {conv['title']}",
                key=f"conv_{conv['id']}"
            ):

                st.session_state.conversation_id = (
                    conv["id"]
                )

                msg_response = requests.get(
                    f"{BACKEND_URL}/messages/{conv['id']}",
                    headers={
                        "token": st.session_state.token
                    }
                )

                if msg_response.status_code == 200:

                    st.session_state.messages = (
                        msg_response.json()
                    )

                else:

                    st.error(
                        "Failed to load messages."
                    )

    else:

        st.error(
            "Failed to load conversations."
        )

    # =================================================
    # FILE UPLOAD
    # =================================================

    st.subheader(
        "Upload Documents"
    )
    st.markdown("""
    ### 📤 Upload Knowledge

    Supported Formats

    PDF • DOCX • TXT • CSV • XLSX • PPTX • Images
    """)
    uploaded_file = st.file_uploader(
        "Upload Documents",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "docx",
            "txt",
            "csv",
            "xlsx",
            "pptx"
        ],
        key=f"upload_{
            st.session_state.uploader_key
        }"
    )

    if uploaded_file:

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file,
                uploaded_file.type
            )
        }

        response = requests.post(
            f"{BACKEND_URL}/upload",
            files=files,
            headers={
                "token": st.session_state.token
            }
        )

        data = response.json()

        if "filename" in data:

            st.success(
                f"Uploaded: "
                f"{data['filename']}"
            )

            st.session_state.uploader_key += 1

            st.rerun()

        else:

            st.error(
                data.get(
                    "message",
                    "Upload failed"
                )
            )

    st.divider()

    # =================================================
    # KNOWLEDGE BASE
    # =================================================

    st.subheader(
        "Knowledge Base"
    )

    try:

        response = requests.get(
            f"{BACKEND_URL}/files",
            headers={
                "token": st.session_state.token
            }
        )

        files = response.json()

        if len(files) == 0:

            st.info(
                "No documents uploaded."
            )

        for file in files:

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.write(
                    f"📄 "
                    f"{file['filename']}"
                )

            with col2:

                if st.button(
                    "❌",
                    key=file["filename"]
                ):

                    delete_response = requests.delete(
                        f"{BACKEND_URL}/delete-file",
                        params={
                            "filename": file[
                                "filename"
                            ]
                        },
                        headers={
                            "token": st.session_state.token
                        }
                    )

                    st.success(
                        delete_response.json().get(
                            "message"
                        )
                    )

                    st.rerun()

    except:

        st.error(
            "Could not fetch files."
        )


# =====================================================
# MAIN PAGE
# =====================================================

st.title(
    "📄 AI-Powered Document Chatbot"
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Documents",
        len(documents)
    )

with col2:

    st.metric(
        "Messages",
        len(
            st.session_state.messages
        )
    )

with col3:

    st.metric(
        "Search Mode",
        (
            "All Files"
            if not st.session_state.selected_file
            else "Single File"
        )
    )

st.divider()

# =====================================================
# SEARCH SCOPE INFO
# =====================================================

if (
    st.session_state.selected_file
):

    st.info(
        f"Searching only in: "
        f"{st.session_state.selected_file}"
    )

else:

    st.markdown("""
    <div style="
    background:#1E293B;
    padding:12px;
    border-radius:12px;
    border:1px solid #334155;
    margin-bottom:15px;
    ">
    🌍 Searching across all uploaded documents
    </div>
    """, unsafe_allow_html=True) 

# =====================================================
# DISPLAY CHAT
# =====================================================

if len(st.session_state.messages) == 0:

    st.markdown("""
    # 🤖 Welcome

    Upload documents and start chatting.

    ### Example Questions

    • Summarize this document

    • Compare two documents

    • Return JSON

    • Analyze an uploaded image
    """)
for idx, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if (
            message["role"] == "assistant"
            and "question" in message
        ):

            pdf_data = generate_pdf_report(
                message["question"],
                message["content"]
            )

            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"report_{idx}.pdf",
                mime="application/pdf",
                key=f"pdf_{idx}"
            )


# =====================================================
# USER INPUT
# =====================================================

query = st.chat_input(
    "Ask a question..."
)

if query:

    # -------------------------------------------------
    # USER MESSAGE
    # -------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    with st.chat_message("user"):

        st.markdown(query)

    # -------------------------------------------------
    # ASSISTANT RESPONSE
    # -------------------------------------------------

    with st.chat_message("assistant"):

        placeholder = st.empty()

        full_response = ""
        thinking = st.empty()
        thinking.info(
            "🤖 Thinking..."
        )

        try:

            response = requests.post(
                f"{BACKEND_URL}/ask",
                json={
                    "query": query,
                    "chat_history": (
                        st.session_state.messages
                    ),
                    "conversation_id": (
                        st.session_state.conversation_id
                    ),
                    "selected_file": (
                        st.session_state.selected_file
                    )
                },
                headers={
                    "token": st.session_state.token
                },
                stream=True
            )

            if (
                "conversation_id"
                in response.headers
            ):

                st.session_state.conversation_id = (
                    response.headers[
                        "conversation_id"
                    ]
                )

            for chunk in response.iter_content(
                chunk_size=1024
            ):

                if chunk:

                    decoded = chunk.decode(
                        "utf-8"
                    )

                    full_response += decoded

                    answer_part = full_response

                    sources_part = ""

                    if "📚 Sources:" in full_response:

                        answer_part = (
                            full_response.split(
                                "📚 Sources:"
                            )[0]
                        )

                        sources_part = (
                            full_response.split(
                                "📚 Sources:"
                            )[1]
                        )

                    placeholder.markdown(
                        answer_part
                    )

                    if sources_part:

                        st.markdown(
                            f"""
                    <div style="
                    background:#1E293B;
                    padding:15px;
                    border-radius:12px;
                    border:1px solid #334155;
                    margin-top:10px;
                    ">
                    <b>📚 Sources</b><br>
                    {sources_part.replace(chr(10), "<br>")}
                    </div>
                    """,
                            unsafe_allow_html=True
                        )

        except Exception as e:

            full_response = (
                f"Error: {str(e)}"
            )

            st.error(full_response)

    # -------------------------------------------------
    # SAVE ASSISTANT MESSAGE
    # -------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "question": query
        }
    )
    pdf_data = generate_pdf_report(
        query,
        full_response
    )

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_data,
        file_name="ai_report.pdf",
        mime="application/pdf"
    )

    try:

        parsed_json = json.loads(
            full_response
        )

        st.download_button(
            label="📥 Download JSON",
            data=json.dumps(
                parsed_json,
                indent=4
            ),
            file_name="response.json",
            mime="application/json"
        )

    except:

        pass

