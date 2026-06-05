import re
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# =====================================================
# PREPROCESSING PIPELINE
# =====================================================

def preprocess_image(image: Image.Image) -> Image.Image:
    """Full preprocessing pipeline: grayscale → upscale → CLAHE → denoise → threshold → deskew."""

    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')

    # Upscale small images to 300 DPI equivalent for better OCR
    w, h = image.size
    if w < 1800:
        scale = max(2, 1800 // w)
        image = image.resize((w * scale, h * scale), Image.LANCZOS)

    # Convert to numpy for OpenCV processing
    arr = np.array(image)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # Gaussian denoise
    arr = cv2.GaussianBlur(arr, (3, 3), 0)

    # Adaptive threshold (binarize)
    arr = cv2.adaptiveThreshold(
        arr, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )

    # Morphological opening to remove noise specks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    arr = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel)

    return Image.fromarray(arr)


# =====================================================
# DESKEW
# =====================================================

def deskew_image(image: Image.Image) -> Image.Image:
    """Detect and correct skew angle using Hough line transform."""
    try:
        arr = np.array(image)
        coords = np.column_stack(np.where(arr < 128))
        if len(coords) < 100:
            return image

        # MinAreaRect on text pixels
        rect = cv2.minAreaRect(coords)
        angle = rect[2]

        if angle < -45:
            angle = 90 + angle

        if abs(angle) > 0.5:
            (h, w) = arr.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            arr = cv2.warpAffine(arr, M, (w, h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)

        return Image.fromarray(arr)
    except Exception:
        return image


# =====================================================
# MULTI-PSM EXTRACTION
# =====================================================

def extract_multi_psm(image: Image.Image) -> str:
    """Try PSM modes 3, 4, 6, 11. Return longest high-quality result."""
    configs = [
        '--oem 3 --psm 6',   # uniform block of text
        '--oem 3 --psm 3',   # fully automatic layout
        '--oem 3 --psm 4',   # single column of text
        '--oem 3 --psm 11',  # sparse text
    ]
    best = ''
    for cfg in configs:
        try:
            text = pytesseract.image_to_string(image, config=cfg, lang='eng')
            text = text.strip()
            if len(re.sub(r'\s+', '', text)) > len(re.sub(r'\s+', '', best)):
                best = text
        except Exception:
            continue
    return best


# =====================================================
# CONFIDENCE-FILTERED EXTRACTION
# =====================================================

def extract_high_confidence(image: Image.Image, min_conf: int = 40) -> str:
    """Extract only words with confidence >= min_conf."""
    try:
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config='--oem 3 --psm 6'
        )
        words = [
            data['text'][i]
            for i in range(len(data['text']))
            if int(data['conf'][i]) >= min_conf and data['text'][i].strip()
        ]
        return ' '.join(words)
    except Exception:
        return ''


# =====================================================
# TABLE EXTRACTION
# =====================================================

def extract_table_text(image: Image.Image) -> str:
    """Detect and extract structured table content from image."""
    try:
        tsv = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config='--oem 3 --psm 6'
        )

        rows: dict = {}
        for i, word in enumerate(tsv['text']):
            if not word.strip() or int(tsv['conf'][i]) < 30:
                continue
            row_key = tsv['top'][i] // 20  # group by vertical position
            rows.setdefault(row_key, []).append(word)

        lines = [' | '.join(words) for _, words in sorted(rows.items())]
        return '\n'.join(lines)
    except Exception:
        return ''


# =====================================================
# MAIN ENTRY POINT
# =====================================================

def extract_text_from_image(image_path: str) -> str:
    """
    Full OCR pipeline:
    preprocess → deskew → multi-PSM → confidence filter → table detect → clean
    """
    try:
        image = Image.open(image_path)

        # Preprocess
        processed = preprocess_image(image)
        processed = deskew_image(processed)

        # Multi-PSM text
        raw_text = extract_multi_psm(processed)

        # Fallback: confidence-filtered if result is thin
        if len(raw_text.strip()) < 80:
            conf_text = extract_high_confidence(processed, min_conf=30)
            if len(conf_text) > len(raw_text):
                raw_text = conf_text

        # Try table extraction and append if found
        table_text = extract_table_text(processed)
        unique_table = table_text if table_text not in raw_text else ''

        combined = raw_text
        if unique_table and len(unique_table) > 50:
            combined += f'\n\n[TABLE CONTENT]\n{unique_table}'

        # Clean up
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        combined = re.sub(r' {2,}', ' ', combined)

        return combined.strip()

    except Exception as e:
        return f"OCR Error: {str(e)}"


# =====================================================
# SCANNED PDF OCR
# =====================================================

def ocr_scanned_pdf(pdf_path: str) -> list:
    """Convert scanned PDF pages to images and run full OCR pipeline."""
    from pdf2image import convert_from_path
    from langchain_core.documents import Document
    import os

    filename = os.path.basename(pdf_path)
    documents = []

    try:
        pages = convert_from_path(pdf_path, dpi=300, fmt='png')
        print(f"Scanned PDF OCR: {len(pages)} pages detected")

        for i, page_pil in enumerate(pages):
            processed = preprocess_image(page_pil)
            processed = deskew_image(processed)
            text = extract_multi_psm(processed)

            # Table detection
            table_text = extract_table_text(processed)
            if table_text and table_text not in text and len(table_text) > 50:
                text += f'\n\n[TABLE CONTENT]\n{table_text}'

            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text).strip()

            if text:
                documents.append(Document(
                    page_content=text,
                    metadata={
                        'source': filename,
                        'page': i,
                        'file_type': 'scanned_pdf',
                        'ocr_processed': True,
                    }
                ))
            else:
                print(f"  Page {i+1}: OCR returned empty")

        print(f"Scanned PDF OCR complete: {len(documents)} pages extracted")
        return documents

    except Exception as e:
        print(f"Scanned PDF OCR failed: {e}")
        return []
