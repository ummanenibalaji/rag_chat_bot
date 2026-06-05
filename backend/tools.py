import math

from duckduckgo_search import DDGS
from vision_utils import (
    analyze_image
)
from cad_checker import (
    validate_document
)
# =====================================================
# CALCULATOR TOOL
# =====================================================

def calculator_tool(
    expression
):

    try:

        allowed_names = {
            "math": math
        }

        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            allowed_names
        )

        return str(result)

    except Exception as e:

        return (
            f"Calculation Error: {str(e)}"
        )


# =====================================================
# WEB SEARCH TOOL
# =====================================================

def web_search_tool(
    query,
    max_results=5
):

    try:

        results = []

        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=max_results
            )

            for result in search_results:

                title = result.get(
                    "title",
                    ""
                )

                body = result.get(
                    "body",
                    ""
                )

                href = result.get(
                    "href",
                    ""
                )

                formatted = (
                    f"Title: {title}\n"
                    f"Snippet: {body}\n"
                    f"Link: {href}\n"
                )

                results.append(
                    formatted
                )

        return "\n\n".join(results)

    except Exception as e:

        return (
            f"Web Search Error: {str(e)}"
        )
        
# =====================================================
# VISION TOOL
# =====================================================

def vision_tool(
    image_path,
    question
):

    try:

        result = analyze_image(
            image_path,
            question
        )

        return result

    except Exception as e:

        return (
            f"Vision Error: {str(e)}"
        )
    
# =====================================================
# CAD REVIEW TOOL
# =====================================================

def cad_review_tool(
    pdf_path
):

    report = validate_document(
        pdf_path
    )

    return report