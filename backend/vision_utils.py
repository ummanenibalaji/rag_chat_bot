from langchain_ollama import ChatOllama

from langchain_core.messages import (
    HumanMessage
)


# =====================================================
# VISION MODEL
# =====================================================

vision_llm = ChatOllama(
    model="gemma3:12b"
)


# =====================================================
# ANALYZE IMAGE
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