import os
import json
import re
import fitz
from PIL import Image

from vision_utils import (
    extract_title_block,
    extract_key_plan,
    extract_drawing_labels
)

# =====================================================
# PDF TO PAGE IMAGES
# =====================================================

def pdf_to_images(
    pdf_path
):

    doc = fitz.open(
        pdf_path
    )

    image_paths = []

    for page_num in range(
        len(doc)
    ):

        page = doc.load_page(
            page_num
        )

        pix = page.get_pixmap(
            matrix=fitz.Matrix(
                5,
                5
            )
        )

        image_path = (
            f"temp_page_{page_num+1}.png"
        )

        pix.save(
            image_path
        )

        image_paths.append(
            image_path
        )

    return image_paths


# =====================================================
# CROP TITLE BLOCK
# =====================================================

def crop_title_block(
    image_path
):

    image = Image.open(
        image_path
    )

    width, height = image.size

    # Entire right-side vertical title block

    left = int(width * 0.88)
    top = 0
    right = width
    bottom = height

    crop = image.crop(
        (
            left,
            top,
            right,
            bottom
        )
    )

    output = (
        image_path.replace(
            ".png",
            "_title.png"
        )
    )

    crop.save(
        output
    )

    print(
        f"TITLE BLOCK CROP SAVED: {output}"
    )

    return output


# =====================================================
# CROP KEY PLAN
# =====================================================

from PIL import ImageDraw

def crop_key_plan(
    image_path
):

    image = Image.open(
        image_path
    )

    width, height = image.size

    left = 0
    top = int(height * 0.78)

    right = int(width * 0.22)
    bottom = height

    crop = image.crop(
        (
            left,
            top,
            right,
            bottom
        )
    )

    output = (
        image_path.replace(
            ".png",
            "_keyplan.png"
        )
    )

    crop.save(
        output
    )

    print(
        f"KEY PLAN CROP SAVED: {output}"
    )

    return output

    # =================================================
    # DEBUG IMAGE
    # =================================================

    debug = image.copy()

    draw = ImageDraw.Draw(
        debug
    )

    draw.rectangle(
        [
            left,
            top,
            right,
            bottom
        ],
        outline="red",
        width=15
    )

    debug_output = (
        image_path.replace(
            ".png",
            "_debug.png"
        )
    )

    debug.save(
        debug_output
    )

    print(
        f"DEBUG IMAGE SAVED: {debug_output}"
    )

    return output

# =====================================================
# CROP DRAWING AREA
# =====================================================

def crop_drawing_area(
    image_path
):

    image = Image.open(
        image_path
    )

    width, height = image.size

    crop = image.crop(
        (
            int(width * 0.20),
            int(height * 0.20),
            int(width * 0.80),
            int(height * 0.80)
        )
    )

    output = (
        image_path.replace(
            ".png",
            "_drawing.png"
        )
    )

    crop.save(
        output
    )

    return output


# =====================================================
# SAFE JSON
# =====================================================

def extract_json(
    text
):

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

            return None

    return None

# =====================================================
# VALIDATE PAGE
# =====================================================

import json

def validate_page(metadata):

    errors = []

    title = metadata.get(
        "title_block",
        {}
    )

    key_plan = metadata.get(
        "key_plan",
        {}
    )

    drawing = metadata.get(
        "drawing",
        {}
    )

    title_array = str(
        title.get("array", "")
    ).strip()

    key_array = str(
        key_plan.get("array", "")
    ).strip()

    drawing_array = str(
        drawing.get("array", "")
    ).strip()

    title_roof = str(
        title.get("roof_area", "")
    ).strip()

    key_roof = str(
        key_plan.get("roof_area", "")
    ).strip()

    drawing_roof = str(
        drawing.get("roof_area", "")
    ).strip()

    print("\n========== PAGE METADATA ==========")
    print(
        json.dumps(
            metadata,
            indent=4
        )
    )
    print("===================================\n")

    print("\n========== VALIDATION ==========")
    print("TITLE ARRAY :", title_array)
    print("KEY ARRAY   :", key_array)
    print("DRAW ARRAY  :", drawing_array)
    print("TITLE ROOF  :", title_roof)
    print("KEY ROOF    :", key_roof)
    print("DRAW ROOF   :", drawing_roof)
    print("================================\n")

    def valid_value(value):

        if value is None:
            return False

        value = str(value).strip().upper()

        invalid_values = [
            "",
            "NOT_FOUND",
            "ARRAY",
            "ROOF AREA",
            "UNKNOWN",
            "N/A",
            "NULL"
        ]

        return value not in invalid_values

    # ----------------------------------
    # TITLE BLOCK vs KEY PLAN
    # ----------------------------------

    if (
        valid_value(title_array)
        and valid_value(key_array)
        and title_array != key_array
    ):
        errors.append(
            "ARRAY_MISMATCH"
        )

    if (
        valid_value(title_roof)
        and valid_value(key_roof)
        and title_roof != key_roof
    ):
        errors.append(
            "ROOF_AREA_MISMATCH"
        )

    # ----------------------------------
    # TITLE BLOCK vs DRAWING
    # ----------------------------------

    # if (
    #     valid_value(title_array)
    #     and valid_value(drawing_array)
    #     and title_array != drawing_array
    # ):
    #     errors.append(
    #         "DRAWING_ARRAY_MISMATCH"
    #     )

    # if (
    #     valid_value(title_roof)
    #     and valid_value(drawing_roof)
    #     and title_roof != drawing_roof
    # ):
    #     errors.append(
    #         "DRAWING_ROOF_AREA_MISMATCH"
    #     )

    print("\n========== ERRORS ==========")
    print(errors)
    print("============================\n")

    return errors

# =====================================================
# VALIDATE DOCUMENT
# =====================================================

def validate_document(
    pdf_path
):

    pages = pdf_to_images(
        pdf_path
    )

    report = []

    for page_no, page_image in enumerate(
        pages,
        start=1
    ):

        print(
            f"\nProcessing Page {page_no}"
        )

        try:

            title_crop = crop_title_block(
                page_image
            )

            key_crop = crop_key_plan(
                page_image
            )

            drawing_crop = crop_drawing_area(
                page_image
            )

            title_data = extract_json(
                extract_title_block(
                    title_crop
                )
            )

            key_data = extract_json(
                extract_key_plan(
                    key_crop
                )
            )

            drawing_data = extract_json(
                extract_drawing_labels(
                    drawing_crop
                )
            )

            print("\nTITLE BLOCK RESPONSE:")
            print(json.dumps(title_data, indent=4))

            print("\nKEY PLAN RESPONSE:")
            print(json.dumps(key_data, indent=4))

            print("\nDRAWING RESPONSE:")
            print(json.dumps(drawing_data, indent=4))

            metadata = {
                "title_block":
                    title_data or {},
                "key_plan":
                    key_data or {},
                "drawing":
                    drawing_data or {}
            }

            print(
                json.dumps(
                    metadata,
                    indent=4
                )
            )

            print("\n========== PAGE METADATA ==========")
            print(
                json.dumps(
                    metadata,
                    indent=4
                )
            )
            print("===================================\n")

            errors = validate_page(
                metadata
            )

            report.append(
                {
                    "page": page_no,
                    "status":
                        "PASS"
                        if len(errors) == 0
                        else "FAIL",
                    "errors": errors,
                    "metadata": metadata
                }
            )

        except Exception as e:

            report.append(
                {
                    "page": page_no,
                    "status": "ERROR",
                    "errors": [
                        str(e)
                    ]
                }
            )

    return report


# =====================================================
# ARRAY DIMENSION EXTRACTION
# =====================================================

_FULL_DIM_RE = re.compile(r"\d+'-\d+(?:\s+\d+/\d+)?\"")
_BASE_DIM_RE = re.compile(r"^\d+'-\d+$")
_FTONLY_RE   = re.compile(r"^\d{2,}'$")   # e.g. "133'" — feet only, no inch part


def _to_inches(s):
    m = re.match(r"(\d+)'-(\d+)", s)
    if m:
        return int(m.group(1)) * 12 + int(m.group(2))
    m2 = re.match(r"(\d+)'$", s)
    if m2:
        return int(m2.group(1)) * 12
    return 0


def _collect_all_dims(page):
    """
    Two-pass dim collection:
    Pass 1 — complete dims already in a single span (e.g. "6'-10 1/2\"").
    Pass 2 — split-span dims where the fraction is rendered as stacked
              superscript/subscript glyphs in separate spans:
              "121'-8" span + "1" (up) + "2" (down) + '"' span → "121'-8 1/2\""
    """
    all_spans = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for line in b["lines"]:
            for span in line["spans"]:
                t = span["text"].strip()
                if not t:
                    continue
                x0, y0, x1, y1 = span["bbox"]
                all_spans.append({
                    "text": t,
                    "cx": (x0 + x1) / 2,
                    "cy": (y0 + y1) / 2,
                })

    dims = []

    # Pass 1: complete dims already in one span
    for s in all_spans:
        for m in _FULL_DIM_RE.finditer(s["text"]):
            dims.append({"val": m.group(), "cx": s["cx"], "cy": s["cy"]})

    # Pass 2: reconstruct split dims
    for s in all_spans:
        if not _BASE_DIM_RE.fullmatch(s["text"]):
            continue
        base_cx, base_cy = s["cx"], s["cy"]

        # Closing " span within 250px right, ±25px vertical
        inch_spans = [
            sp for sp in all_spans
            if sp["text"] == '"'
            and 10 < sp["cx"] - base_cx < 250
            and abs(sp["cy"] - base_cy) < 25
        ]
        if not inch_spans:
            continue
        inch = min(inch_spans, key=lambda sp: sp["cx"] - base_cx)

        # Single-digit spans between base and " (stacked fraction glyphs)
        frac = [
            sp for sp in all_spans
            if sp["text"].isdigit()
            and base_cx < sp["cx"] < inch["cx"]
            and abs(sp["cy"] - base_cy) < 35
        ]

        if len(frac) == 2:
            num, den = sorted(frac, key=lambda sp: sp["cy"])
            val = f"{s['text']} {num['text']}/{den['text']}\""
        else:
            val = f"{s['text']}\""

        dims.append({"val": val, "cx": base_cx, "cy": base_cy})

    # Pass 3: feet-only dims like "133'" (no inch component)
    for s in all_spans:
        if _FTONLY_RE.fullmatch(s["text"]):
            dims.append({"val": s["text"], "cx": s["cx"], "cy": s["cy"]})

    return dims


def extract_array_dimensions(pdf_path: str) -> dict:
    """
    Extract overall array width and height per page from a CAD PDF.

    Uses embedded text + bounding-box coordinates (no OCR needed).
    Repeating dims = panel dims (cluster). Overall dims sit spatially
    outside the cluster: above → width, right of → height.

    Returns:
        {
          1: {"width": "114'-2\"",  "height": "31'-6\"",  "source": "text"},
          2: {"width": None,        "height": None,        "source": "not_found"},
          ...
        }
    """
    from collections import Counter

    doc = fitz.open(pdf_path)
    results = {}

    for pg in range(len(doc)):
        page = doc[pg]
        all_dims = _collect_all_dims(page)

        if not all_dims:
            results[pg + 1] = {"width": None, "height": None, "source": "not_found"}
            continue

        counts = Counter(d["val"] for d in all_dims)

        # Panel cluster = repeating dims
        repeating = [d for d in all_dims if counts[d["val"]] > 1]
        cluster_min_cy = min(d["cy"] for d in repeating) if repeating else float("inf")
        cluster_max_cx = max(d["cx"] for d in repeating) if repeating else 0.0

        GAP = 60
        width_cands  = [d for d in all_dims if d["cy"] < cluster_min_cy - GAP]
        height_cands = [d for d in all_dims if d["cx"] > cluster_max_cx + GAP]

        def pick_best(cands):
            if not cands:
                return None
            unique = [d for d in cands if counts[d["val"]] == 1]
            pool = unique if unique else cands
            return max(pool, key=lambda d: _to_inches(d["val"]))["val"]

        width_val  = pick_best(width_cands)
        height_val = pick_best(height_cands)

        results[pg + 1] = {
            "width":  width_val,
            "height": height_val,
            "source": "text" if (width_val or height_val) else "not_found",
        }

    return results