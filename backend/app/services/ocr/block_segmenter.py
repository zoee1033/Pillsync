import os
import time
import json
import logging
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

logger = logging.getLogger("BLOCK_SEGMENTER")

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))


def segment_prescription_blocks(
    img: np.ndarray,
    debug: bool = False,
    debug_dir: Optional[str] = None
) -> Tuple[List[Tuple[np.ndarray, Tuple[int, int, int, int]]], Dict[str, Any]]:
    """
    Intelligent Medicine Block Segmentation Layer:
    1. Receives OpenCV enhanced image array.
    2. Detects text regions & medicine blocks using OpenCV contour analysis and morph dilation.
    3. Excludes page borders, letterheads (top ~15-20%), doctor signatures (bottom ~10-15%), and margins.
    4. Merges multi-line medicine blocks (e.g. Tab Calpol \n 500 mg \n 1-0-1 \n 5 Days) into ONE block crop.
    5. Adds 5-15px padding around crops and maintains Top->Bottom, Left->Right reading order.
    6. Automatically falls back to full image if confidence < 0.50 or 0 blocks detected.
    7. Saves debug visualizations if debug=True or DEBUG_OCR=True.
    """
    start_time = time.time()

    if debug_dir is None:
        debug_dir = DEBUG_DIR

    is_debug = debug or DEBUG_OCR

    if img is None or img.size == 0:
        elapsed_ms = (time.time() - start_time) * 1000.0
        meta = {
            "block_count": 0,
            "bounding_boxes": [],
            "average_crop_size": (0.0, 0.0),
            "segmentation_confidence": 0.0,
            "fallback_used": True,
            "execution_time_ms": round(elapsed_ms, 2)
        }
        return [], meta

    # Handle grayscale or BGR
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    h, w = gray.shape[:2]
    total_area = float(h * w)

    # 1. Page margin and letterhead / footer exclusion bounds
    top_letterhead_bound = int(h * 0.10)
    bottom_signature_bound = int(h * 0.92)

    # 2. Binarization for text component extraction (Dark ink on light paper)
    # Use THRESH_BINARY_INV so ink text becomes white foreground (255)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Handle inverted dark-mode images if foreground ratio exceeds 50%
    if (cv2.countNonZero(thresh) / total_area) > 0.50:
        thresh = cv2.bitwise_not(thresh)

    non_zero = cv2.countNonZero(thresh)
    if non_zero < 50 or (non_zero / total_area) < 0.002:
        elapsed_ms = (time.time() - start_time) * 1000.0
        meta = {
            "block_count": 1,
            "bounding_boxes": [[0, 0, w, h]],
            "average_crop_size": (float(w), float(h)),
            "segmentation_confidence": 1.0,
            "fallback_used": True,
            "execution_time_ms": round(elapsed_ms, 2)
        }
        logger.info(f"[BLOCK_SEGMENTER] Blank or low contrast image. Fallback triggered. ({meta['execution_time_ms']} ms)")
        return [(img.copy(), (0, 0, w, h))], meta

    # 3. Morphological Dilation to connect text lines belonging to the same medicine block
    k_w = max(12, int(w * 0.035))
    k_h = max(6, int(h * 0.015))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_w, k_h))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 4. Find external contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidate_boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        box_area = bw * bh

        # Exclude tiny noise spots or massive full-page border contours
        if bw < 25 or bh < 12 or box_area < 200:
            continue
        if bw > 0.96 * w and bh > 0.96 * h:
            continue

        # Exclude regions located entirely within doctor letterhead top area or signature bottom area
        if y < top_letterhead_bound and bh < int(h * 0.08):
            continue
        if y > bottom_signature_bound and bh < int(h * 0.08):
            continue

        candidate_boxes.append((x, y, bw, bh))

    # 5. Multi-Line Medicine Block Merging
    candidate_boxes.sort(key=lambda b: b[1])
    merged_boxes: List[Tuple[int, int, int, int]] = []

    for box in candidate_boxes:
        if not merged_boxes:
            merged_boxes.append(box)
        else:
            prev_x, prev_y, prev_w, prev_h = merged_boxes[-1]
            curr_x, curr_y, curr_w, curr_h = box

            v_gap = curr_y - (prev_y + prev_h)
            h_overlap = min(prev_x + prev_w, curr_x + curr_w) - max(prev_x, curr_x)
            min_w = min(prev_w, curr_w)
            h_overlap_ratio = (h_overlap / float(min_w)) if min_w > 0 else 0.0

            # Merge lines if vertical gap is small (< 30px or < 4% height) and horizontal overlap/alignment is present
            max_v_gap = max(28, int(h * 0.04))
            if v_gap <= max_v_gap and (h_overlap_ratio > 0.20 or abs(curr_x - prev_x) < 60):
                new_x = min(prev_x, curr_x)
                new_y = min(prev_y, curr_y)
                new_w = max(prev_x + prev_w, curr_x + curr_w) - new_x
                new_h = max(prev_y + prev_h, curr_y + curr_h) - new_y
                merged_boxes[-1] = (new_x, new_y, new_w, new_h)
            else:
                merged_boxes.append(box)

    # 6. Sorting Reading Order (Top -> Bottom, Left -> Right)
    merged_boxes.sort(key=lambda b: (b[1] // 30, b[0]))

    # 7. Extract Crops with 5-15px Padding (Default: 10px)
    crops: List[Tuple[np.ndarray, Tuple[int, int, int, int]]] = []
    padding = 10
    total_segmented_area = 0.0

    for x, y, bw, bh in merged_boxes:
        pad_x1 = max(0, x - padding)
        pad_y1 = max(0, y - padding)
        pad_x2 = min(w, x + bw + padding)
        pad_y2 = min(h, y + bh + padding)

        crop_w = pad_x2 - pad_x1
        crop_h = pad_y2 - pad_y1

        if crop_w < 15 or crop_h < 15:
            continue

        crop_img = img[pad_y1:pad_y2, pad_x1:pad_x2].copy()
        crops.append((crop_img, (pad_x1, pad_y1, crop_w, crop_h)))
        total_segmented_area += (crop_w * crop_h)

    # 8. Fallback Evaluation
    block_count = len(crops)
    coverage_ratio = total_segmented_area / total_area if total_area > 0 else 0.0

    if block_count == 0:
        segmentation_confidence = 0.0
    elif block_count > 20:
        segmentation_confidence = 0.35
    else:
        segmentation_confidence = min(0.98, round(0.55 + (coverage_ratio * 0.35) + (block_count * 0.03), 2))

    fallback_used = False
    if block_count == 0 or segmentation_confidence < 0.50:
        fallback_used = True
        crops = [(img.copy(), (0, 0, w, h))]

    elapsed_ms = (time.time() - start_time) * 1000.0

    avg_w = sum(c[1][2] for c in crops) / float(len(crops)) if crops else 0.0
    avg_h = sum(c[1][3] for c in crops) / float(len(crops)) if crops else 0.0

    meta = {
        "block_count": len(crops),
        "bounding_boxes": [[c[1][0], c[1][1], c[1][2], c[1][3]] for c in crops],
        "average_crop_size": (round(avg_w, 1), round(avg_h, 1)),
        "segmentation_confidence": segmentation_confidence if not fallback_used else 1.0,
        "fallback_used": fallback_used,
        "execution_time_ms": round(elapsed_ms, 2)
    }

    logger.info(
        f"[BLOCK_SEGMENTER] Detected {meta['block_count']} blocks "
        f"(Avg Size: {meta['average_crop_size']}, Conf: {meta['segmentation_confidence']:.2f}, "
        f"Time: {meta['execution_time_ms']} ms, Fallback: {meta['fallback_used']})"
    )

    # 9. Save Debug Outputs if Requested
    if is_debug:
        try:
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, "original.png"), img)
            cv2.imwrite(os.path.join(debug_dir, "preprocessed.png"), gray)

            debug_viz = img.copy()
            if len(debug_viz.shape) == 2:
                debug_viz = cv2.cvtColor(debug_viz, cv2.COLOR_GRAY2BGR)

            for idx, (c_img, (bx, by, bw_c, bh_c)) in enumerate(crops, 1):
                color = (0, 255, 0) if not fallback_used else (0, 0, 255)
                cv2.rectangle(debug_viz, (bx, by), (bx + bw_c, by + bh_c), color, 2)
                cv2.putText(
                    debug_viz, f"Block #{idx}", (bx, max(18, by - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
                )
                cv2.imwrite(os.path.join(debug_dir, f"crop_{idx}.png"), c_img)

            cv2.imwrite(os.path.join(debug_dir, "detected_blocks.png"), debug_viz)

            with open(os.path.join(debug_dir, "block_coordinates.json"), "w", encoding="utf-8") as f_json:
                json.dump(meta, f_json, indent=2)

        except Exception as dbg_err:
            logger.warning(f"[BLOCK_SEGMENTER] Debug save error: {dbg_err}")

    return crops, meta
