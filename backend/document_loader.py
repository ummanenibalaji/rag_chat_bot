import os
from datetime import datetime

from langchain_community.document_loaders import (
    PyPDFLoader
)

from langchain_core.documents import (
    Document
)

from ocr_utils import (
    extract_text_from_image
)

from docx import Document as DocxDocument

from pptx import Presentation

import pandas as pd

# =====================================================
# COMMON METADATA
# =====================================================

def build_metadata(
    file_path,
    file_type,
    page=None
):

    filename = os.path.basename(
        file_path
    )

    metadata = {
        "source": filename,
        "file_name": filename,
        "file_type": file_type,
        "document_id": filename.replace(
            ".", "_"
        ),
        "upload_time": str(
            datetime.now()
        )
    }

    if page is not None:

        metadata["page"] = page

    return metadata


# =====================================================
# LOAD PDF
# =====================================================

def load_pdf(
    file_path
):

    loader = PyPDFLoader(
        file_path
    )

    documents = loader.load()

    for doc in documents:

        page_number = doc.metadata.get(
            "page",
            0
        )

        doc.metadata.update(
            build_metadata(
                file_path=file_path,
                file_type="pdf",
                page=page_number
            )
        )

    return documents


# =====================================================
# LOAD IMAGE USING OCR
# =====================================================

def load_image(
    file_path
):

    extracted_text = extract_text_from_image(
        file_path
    )

    document = Document(
        page_content=extracted_text,
        metadata=build_metadata(
            file_path=file_path,
            file_type="image"
        )
    )

    return [document]

# =====================================================
# LOAD DOCX
# =====================================================

def load_docx(
    file_path
):

    doc = DocxDocument(
        file_path
    )

    text = "\n".join(
        [
            paragraph.text
            for paragraph in doc.paragraphs
        ]
    )

    return [
        Document(
            page_content=text,
            metadata={
                "source": os.path.basename(
                    file_path
                ),
                "type": "docx"
            }
        )
    ]

# =====================================================
# LOAD TXT
# =====================================================

def load_txt(
    file_path
):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        text = f.read()

    return [
        Document(
            page_content=text,
            metadata={
                "source": os.path.basename(
                    file_path
                ),
                "type": "txt"
            }
        )
    ]

# =====================================================
# LOAD CSV
# =====================================================

def load_csv(
    file_path
):

    df = pd.read_csv(
        file_path
    )

    text = df.to_string()

    return [
        Document(
            page_content=text,
            metadata={
                "source": os.path.basename(
                    file_path
                ),
                "type": "csv"
            }
        )
    ]

# =====================================================
# LOAD XLSX
# =====================================================

def load_xlsx(
    file_path
):

    df = pd.read_excel(
        file_path
    )

    text = df.to_string()

    return [
        Document(
            page_content=text,
            metadata={
                "source": os.path.basename(
                    file_path
                ),
                "type": "xlsx"
            }
        )
    ]

# =====================================================
# LOAD PPTX
# =====================================================

def load_pptx(
    file_path
):

    prs = Presentation(
        file_path
    )

    text = ""

    for slide in prs.slides:

        for shape in slide.shapes:

            if hasattr(
                shape,
                "text"
            ):

                text += (
                    shape.text + "\n"
                )

    return [
        Document(
            page_content=text,
            metadata={
                "source": os.path.basename(
                    file_path
                ),
                "type": "pptx"
            }
        )
    ]

# =====================================================
# UNIVERSAL DOCUMENT LOADER
# =====================================================

def load_document(
    file_path
):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    # -------------------------------------------------
    # PDF
    # -------------------------------------------------

    if extension == ".pdf":

        return load_pdf(
            file_path
        )
    if extension == ".docx":

        return load_docx(
            file_path
        )

    if extension == ".txt":

        return load_txt(
            file_path
        )

    if extension == ".csv":

        return load_csv(
            file_path
        )

    if extension == ".xlsx":

        return load_xlsx(
            file_path
        )

    if extension == ".pptx":

        return load_pptx(
            file_path
        )
    # -------------------------------------------------
    # IMAGES
    # -------------------------------------------------

    image_extensions = [
        ".png",
        ".jpg",
        ".jpeg"
    ]

    if extension in image_extensions:

        return load_image(
            file_path
        )

    # -------------------------------------------------
    # UNSUPPORTED
    # -------------------------------------------------

    raise ValueError(
        f"Unsupported file type: {extension}"
    )