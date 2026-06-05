from urllib import response

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

import json
import re
import pytesseract
import re
from PIL import Image
# =====================================================
# VISION MODEL
# =====================================================

vision_llm = ChatOllama(
    model="gemma3:12b"
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

- engineering_drawing
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

Return ONLY the category.
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
# GENERAL IMAGE ANALYSIS
# =====================================================

def analyze_image(
    image_path,
    question
):

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": question
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

# =====================================================
# CLEAN JSON
# =====================================================

def clean_json_response(
    text
):

    if not text:

        return None

    try:

        return json.loads(
            text
        )

    except:

        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:

        try:

            return json.loads(
                match.group()
            )

        except:

            pass

    return None

# =====================================================
# TITLE BLOCK EXTRACTION
# =====================================================

def extract_title_block(
    image_path
):

    try:

        print("\n====================================")
        print("TITLE BLOCK EXTRACTION STARTED")
        print("IMAGE PATH:", image_path)

        img = Image.open(image_path)

        ocr_text = pytesseract.image_to_string(img)

        print("\n========== TITLE OCR ==========")
        print(ocr_text)
        print("================================")

        roof_area = "NOT_FOUND"
        array_num = "NOT_FOUND"
        sheet_num = "NOT_FOUND"

        roof_match = re.search(
            r"ROOF\s*AREA\s*(\d+)",
            ocr_text,
            re.IGNORECASE
        )

        if roof_match:
            roof_area = roof_match.group(1)

        array_matches = re.findall(
            r"ARRAY\s*(\d+)",
            ocr_text,
            re.IGNORECASE
        )

        if array_matches:
            array_num = array_matches[-1]

        sheet_match = re.search(
            r"(?:SM|OM)\.?\s*(\d+)",
            ocr_text,
            re.IGNORECASE
        )

        if sheet_match:
            sheet_num = sheet_match.group(1)

        result = {
            "roof_area": roof_area,
            "array": array_num,
            "sheet": sheet_num
        }

        print("\nTITLE BLOCK OCR RESULT:")
        print(result)

        return json.dumps(result)

    except Exception as e:

        print(
            "TITLE BLOCK ERROR:",
            e
        )

        return json.dumps(
            {
                "roof_area": "NOT_FOUND",
                "array": "NOT_FOUND",
                "sheet": "NOT_FOUND"
            }
        )
# =====================================================
# KEY PLAN EXTRACTION
# =====================================================

def extract_key_plan(
    image_path
):

    try:

        img = Image.open(image_path)

        ocr_text = pytesseract.image_to_string(img)

        print("\n========== KEY PLAN OCR ==========")
        print(ocr_text)
        print("===================================")

        roof_area = "NOT_FOUND"
        array_num = "NOT_FOUND"

        # Match:
        # ROOF AREA 1
        # ROOF AREA 2
        roof_match = re.search(
            r"ROOF\s*AREA\s*(\d+)",
            ocr_text,
            re.IGNORECASE
        )

        if roof_match:
            roof_area = roof_match.group(1)

        # Match:
        # ARRAY 1
        # ARRAY 12
        # ARRAY 63
        array_match = re.search(
            r"ARRAY\s*(\d+)",
            ocr_text,
            re.IGNORECASE
        )

        if array_match:
            array_num = array_match.group(1)

        result = {
            "roof_area": roof_area,
            "array": array_num
        }

        print("\n========== KEY PLAN OCR RESULT ==========")
        print(result)
        print("==========================================")

        return json.dumps(result)

    except Exception as e:

        print(
            "KEY PLAN ERROR:",
            e
        )

        return json.dumps(
            {
                "roof_area": "NOT_FOUND",
                "array": "NOT_FOUND"
            }
        )

# =====================================================
# DRAWING LABEL EXTRACTION
# =====================================================

def extract_drawing_labels(
    image_path
):

    prompt = """
You are an engineering drawing reviewer.

Analyze ONLY the main drawing.

Extract:

{
    "roof_area":"",
    "array":""
}

Rules:
- Return valid JSON only
- No markdown
- No explanation
- If value missing return NOT_FOUND
"""

    try:

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt
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

        print(
            "\nDRAWING RESPONSE:"
        )

        print(
            response.content
        )

        return response.content

    except Exception as e:

        print(e)

        return json.dumps(
            {
                "roof_area": "NOT_FOUND",
                "array": "NOT_FOUND"
            }
        )

# =====================================================
# FULL DRAWING EXTRACTION
# =====================================================

def extract_drawing_metadata(
    image_path
):

    prompt = """
You are a professional CAD QA system.

Carefully inspect the engineering drawing.

Extract:

{
  "title_block": {
    "roof_area": "",
    "array": "",
    "sheet": ""
  },

  "key_plan": {
    "roof_area": "",
    "array": ""
  },

  "drawing": {
    "roof_area": "",
    "array": ""
  },

  "confidence": ""
}

Rules:

- Return JSON only
- No markdown
- No explanations
- Use NOT_FOUND if unavailable
"""

    try:

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt
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

        print(
            "\n========== RAW CAD RESPONSE =========="
        )

        print(
            response.content
        )

        print(
            "======================================"
        )

        cleaned = clean_json_response(
            response.content
        )

        if cleaned:

            return json.dumps(
                cleaned
            )

        return json.dumps(
            {
                "title_block": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND",
                    "sheet": "NOT_FOUND"
                },
                "key_plan": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND"
                },
                "drawing": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND"
                },
                "confidence": "LOW"
            }
        )

    except Exception as e:

        print(
            f"CAD Extraction Error: {e}"
        )

        return json.dumps(
            {
                "title_block": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND",
                    "sheet": "NOT_FOUND"
                },
                "key_plan": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND"
                },
                "drawing": {
                    "roof_area": "NOT_FOUND",
                    "array": "NOT_FOUND"
                },
                "confidence": "ERROR"
            }
        )