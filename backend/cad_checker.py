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