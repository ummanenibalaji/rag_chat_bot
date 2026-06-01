import pytesseract

from PIL import Image


# =====================================================
# OCR IMAGE EXTRACTION
# =====================================================

def extract_text_from_image(
    image_path
):

    try:

        image = Image.open(
            image_path
        )

        text = pytesseract.image_to_string(
            image
        )

        return text.strip()

    except Exception as e:

        return (
            f"OCR Error: {str(e)}"
        )