import os
import re
import time
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("PRESCRIPTION_INTELLIGENCE")

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))

MEDICINE_PREFIX_PATTERN = r'^\s*(?:Tab\.?|Tablet|Cap\.?|Capsule|Syp\.?|Syrup|Inj\.?|Injection|Oint\.?|Ointment|Drops?|Respule|Nebule|Cream|Gel|Susp\.?|Suspension|Rx|Take)\b'
BULLET_PATTERN = r'^\s*(?:\d+[\.\)]|[\bullet\*\•])\s*'
DOSAGE_PATTERN = r'\b\d+\s*(?:mg|g|ml|mcg|iu|puffs?|drops?|tsp|tablets?|caps?)\b'
FREQ_PATTERN = r'\b(?:od|qd|bd|bid|tds|tid|qid|hs|sos|prn|stat|weekly|q6h|q8h|1-0-0|1-0-1|1-1-0|1-1-1|1-1-1-1|0-1-0|0-0-1|once\s+daily|twice\s+daily|thrice\s+daily|alternate\s+day)\b'
DURATION_PATTERN = r'\b(?:\d+\s*(?:d|days?|w|weeks?|months?)|continue|till\s+review|x\s*\d+\s*d(?:ays)?|for\s*\d+\s*d(?:ays)?)\b'
INSTRUCTION_PATTERN = r'\b(?:before\s+food|after\s+food|with\s+food|empty\s+stomach|bedtime|morning|night|as\s+required|ac|pc|bbf)\b'

NON_PRESCRIPTION_PATTERNS = [
    r'^\s*(?:doctor|dr|mbbs|m\.d|m\.s|bams|bhms|dnb|paediatrics|physician|surgeon|specialist|chc|hospital|clinic|nursing\s+home)\b',
    r'^\s*(?:reg|regn|registration|license|licence|ph|phone|tel|mob|contact)\b',
    r'^\s*(?:name|patient\s*name|age|gender|sex|weight|height|date|time|ref|case|opd|ipd)\s*[:\-]',
    r'^\s*(?:clinical\s*description|diagnosis|symptoms|history|examination|investigation|rx\s*date|advice|notes)',
    r'^\s*(?:urti|rr\s*-\s*\d+|rs\s*-\s*b/l|bp\s*-\s*\d+|pulse|temp|spo2)\b',
    r'^\s*(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\s*$',
    r'^\s*(?:gu|mic|standard|sr\s*no|sn|ref\s*no)',
]


def is_non_prescription_header(line: str) -> bool:
    """Filters out non-prescription section headers (doctor info, patient info, dates, clinical noise)."""
    line_clean = line.strip().lower()
    if not line_clean or len(line_clean) < 2:
        return True
    for pattern in NON_PRESCRIPTION_PATTERNS:
        if re.search(pattern, line_clean, re.IGNORECASE):
            return True
    return False


def is_new_block_start(line: str, is_first: bool) -> bool:
    """Determines whether a line marks the start of a new medicine block."""
    if is_first:
        return True

    # Do not start a new block if line is purely an instruction (e.g. After Food, Before Food)
    if re.search(r'^\s*' + INSTRUCTION_PATTERN, line, re.IGNORECASE):
        return False

    # Bullet / Numbering e.g. 1., 2., •
    if re.match(BULLET_PATTERN, line):
        return True

    # Medicine prefix e.g. Tab, Syp, Cap, Inj, Rx
    if re.search(MEDICINE_PREFIX_PATTERN, line, re.IGNORECASE):
        return True

    # Capitalized medicine brand name without pure frequency/duration
    line_clean = line.strip()
    words = line_clean.split()
    if words and len(words[0]) >= 3 and words[0][0].isupper() and words[0].isalpha():
        if not re.search(FREQ_PATTERN, line_clean, re.IGNORECASE) and not re.search(DURATION_PATTERN, line_clean, re.IGNORECASE):
            return True

    return False


def build_block_structure(lines: List[str]) -> Dict[str, Any]:
    """Structures extracted lines into a clean medicine block representation."""
    full_block_text = " ".join(lines)

    # Extract detected components without guessing missing ones
    dosage_match = re.search(DOSAGE_PATTERN, full_block_text, re.IGNORECASE)
    freq_match = re.search(FREQ_PATTERN, full_block_text, re.IGNORECASE)
    duration_match = re.search(DURATION_PATTERN, full_block_text, re.IGNORECASE)
    instruction_match = re.search(INSTRUCTION_PATTERN, full_block_text, re.IGNORECASE)

    return {
        "medicine_lines": lines,
        "dosage": dosage_match.group(0) if dosage_match else "",
        "frequency": freq_match.group(0) if freq_match else "",
        "duration": duration_match.group(0) if duration_match else "",
        "instructions": instruction_match.group(0) if instruction_match else "",
        "confidence": 0.95 if lines else 0.0
    }


def process_prescription_intelligence(
    raw_text: str,
    debug: bool = False,
    debug_dir: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Prescription Intelligence Layer:
    Transforms raw OCR text into structured prescription medicine blocks before parser execution.
    Execution latency strictly < 20 ms.
    """
    start_time = time.perf_counter()

    if debug_dir is None:
        debug_dir = DEBUG_DIR

    is_debug = debug or DEBUG_OCR

    if not raw_text or not raw_text.strip():
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        meta = {
            "group_count": 0,
            "avg_lines_per_group": 0.0,
            "group_confidence": 1.0,
            "execution_time_ms": round(elapsed_ms, 2),
            "fallback_used": True
        }
        return [], meta

    raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    blocks: List[Dict[str, Any]] = []
    current_lines: List[str] = []

    for line in raw_lines:
        if is_non_prescription_header(line):
            continue

        if is_new_block_start(line, len(blocks) == 0 and len(current_lines) == 0):
            if current_lines:
                blocks.append(build_block_structure(current_lines))
                current_lines = []

        current_lines.append(line)

    if current_lines:
        blocks.append(build_block_structure(current_lines))

    # Evaluate Grouping Confidence
    group_count = len(blocks)
    total_lines = sum(len(b["medicine_lines"]) for b in blocks)
    avg_lines = total_lines / float(group_count) if group_count > 0 else 0.0

    fallback_used = False
    if group_count == 0:
        group_confidence = 0.0
        fallback_used = True
    else:
        group_confidence = round(min(0.98, 0.75 + (0.04 * min(group_count, 5)) + (0.03 * min(avg_lines, 4))), 2)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    meta = {
        "group_count": group_count,
        "avg_lines_per_group": round(avg_lines, 2),
        "group_confidence": group_confidence,
        "execution_time_ms": round(elapsed_ms, 2),
        "fallback_used": fallback_used
    }

    logger.info(
        f"[PRESCRIPTION_INTELLIGENCE] Grouped {group_count} blocks "
        f"(Avg Lines: {meta['avg_lines_per_group']}, Conf: {meta['group_confidence']:.2f}, "
        f"Time: {meta['execution_time_ms']} ms)"
    )

    # Save Debug Output Files if Enabled
    if is_debug:
        try:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "grouped_blocks.json"), "w", encoding="utf-8") as f_json:
                json.dump({"metadata": meta, "blocks": blocks}, f_json, indent=2)

            with open(os.path.join(debug_dir, "group_visualization.txt"), "w", encoding="utf-8") as f_txt:
                f_txt.write("=== PRESCRIPTION INTELLIGENCE GROUPING VISUALIZATION ===\n")
                f_txt.write(
                    f"Group Count: {group_count} | Avg Lines: {meta['avg_lines_per_group']} | "
                    f"Confidence: {group_confidence} | Time: {meta['execution_time_ms']} ms\n\n"
                )
                for idx, blk in enumerate(blocks, 1):
                    f_txt.write(f"--- BLOCK #{idx} (Conf: {blk.get('confidence', 0.95)}) ---\n")
                    for line_item in blk.get("medicine_lines", []):
                        f_txt.write(f"  > {line_item}\n")
                    f_txt.write("\n")
        except Exception as dbg_err:
            logger.warning(f"[PRESCRIPTION_INTELLIGENCE] Debug save error: {dbg_err}")

    return blocks, meta
