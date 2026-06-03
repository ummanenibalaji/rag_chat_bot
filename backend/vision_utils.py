import easyocr

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


# =====================================================
# VISION MODEL
# =====================================================

vision_llm = ChatOllama(
    model="gemma3:12b"
)


# =====================================================
# OCR READER
# =====================================================

ocr_reader = easyocr.Reader(
    ["en"],
    gpu=False
)


# =====================================================
# OCR EXTRACTION
# =====================================================

def extract_text_from_image(
    image_path
):

    try:

        results = ocr_reader.readtext(
            image_path,
            detail=0
        )

        return "\n".join(
            results
        )

    except Exception as e:

        return (
            f"OCR Error: {str(e)}"
        )


# =====================================================
# AUTO DOCUMENT DETECTION
# =====================================================

def detect_document_type(
    image_path
):

    try:

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """
Classify this image into ONE category only.

Possible Categories:

- invoice
- resume
- contract
- chart
- table
- dashboard
- screenshot
- receipt
- photo
- other

Return ONLY the category name.
"""
                },
                {
                    "type": "image_url",
                    "image_url": image_path
                }
            ]
        )

        response = vision_llm.invoke(
            [message]
        )

        return (
            response.content
            .strip()
            .lower()
        )

    except Exception:

        return "other"


# =====================================================
# QUERY CLASSIFICATION
# =====================================================

def classify_image_task(
    question
):

    q = question.lower()

    if any(
        x in q
        for x in [
            "table",
            "rows",
            "columns",
            "spreadsheet"
        ]
    ):
        return "table"

    if any(
        x in q
        for x in [
            "chart",
            "graph",
            "plot"
        ]
    ):
        return "chart"

    if any(
        x in q
        for x in [
            "invoice",
            "bill",
            "receipt"
        ]
    ):
        return "invoice"

    if any(
        x in q
        for x in [
            "resume",
            "cv"
        ]
    ):
        return "resume"

    if any(
        x in q
        for x in [
            "contract",
            "agreement"
        ]
    ):
        return "contract"

    if any(
        x in q
        for x in [
            "error",
            "debug",
            "exception",
            "screenshot"
        ]
    ):
        return "screenshot"

    if any(
        x in q
        for x in [
            "dashboard",
            "analytics",
            "kpi"
        ]
    ):
        return "dashboard"

    return "general"


# =====================================================
# PROMPT BUILDER
# =====================================================

def build_vision_prompt(
    task,
    question
):

    prompts = {

        "table": f"""
You are an expert table extraction system.

Extract:
- Column Names
- Rows
- Missing Values
- Summary

Return in a structured format.

Question:
{question}
""",

        "chart": f"""
You are a chart intelligence system.

Analyze:
1. Chart Type
2. Trend
3. Highest Value
4. Lowest Value
5. Outliers
6. Key Insights
7. Business Recommendations

Question:
{question}
""",

        "invoice": f"""
You are an invoice extraction system.

Extract:
- Vendor
- Invoice Number
- Date
- Tax
- Amount
- Currency
- Line Items

Question:
{question}
""",

        "resume": f"""
You are a professional resume parser.

Extract:
- Name
- Email
- Phone
- Skills
- Experience
- Education
- Certifications
- Projects

Question:
{question}
""",

        "contract": f"""
You are a legal contract analyzer.

Identify:
- Parties
- Obligations
- Risks
- Deadlines
- Important Clauses
- Missing Information

Question:
{question}
""",

        "dashboard": f"""
You are a business intelligence analyst.

Analyze:
- KPIs
- Metrics
- Trends
- Anomalies
- Recommendations

Question:
{question}
""",

        "screenshot": f"""
You are a senior software engineer.

Analyze the screenshot carefully.

Return:
1. Error Message
2. Root Cause
3. Exact Fix
4. Code Changes Needed
5. Prevention Tips

Question:
{question}
"""
    }

    return prompts.get(
        task,
        f"""
You are an advanced visual reasoning AI.

Analyze the image in detail.

Question:
{question}
"""
    )


# =====================================================
# ANALYZE IMAGE
# =====================================================

def analyze_image(
    image_path,
    question
):

    task = classify_image_task(
        question
    )

    if task == "general":

        detected_type = detect_document_type(
            image_path
        )

        if detected_type in [
            "invoice",
            "resume",
            "contract",
            "chart",
            "table",
            "dashboard",
            "screenshot"
        ]:

            task = detected_type

    vision_prompt = build_vision_prompt(
        task,
        question
    )

    ocr_text = extract_text_from_image(
        image_path
    )

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"""
{vision_prompt}

OCR EXTRACTED TEXT:

{ocr_text}

Use:
1. OCR text
2. Visual understanding

to provide the most accurate answer possible.
"""
            },
            {
                "type": "image_url",
                "image_url": image_path
            }
        ]
    )

    response = vision_llm.invoke(
        [message]
    )

    return response.content