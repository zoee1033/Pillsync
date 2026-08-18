import re
from typing import List, Tuple, Dict, Any
from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz, validate_dosage_non_destructive, load_medicine_database

ABBREVIATIONS_MAP = {
    r'\b(od|qd|1-0-0)\b': "Once daily",
    r'\b(bd|bid|1-0-1|1-1-0)\b': "Twice daily",
    r'\b(tds|tid|1-1-1)\b': "Three times daily",
    r'\b(qid|q6h|1-1-1-1)\b': "Four times daily",
    r'\b(hs|0-0-1)\b': "At bedtime",
    r'\b(sos|prn)\b': "As needed",
    r'\b(stat)\b': "Immediately",
    r'\b(weekly|1x/wk)\b': "Weekly"
}

# Non-prescription header, patient demographic, and clinical diagnosis patterns
NON_PRESCRIPTION_PATTERNS = [
    r'^\s*(?:doctor|dr|mbbs|m\.d|m\.s|bams|bhms|dnb|paediatrics|physician|surgeon|specialist|chc|hospital|clinic|nursing\s+home)\b',
    r'^\s*(?:reg|regn|registration|license|licence|ph|phone|tel|mob|contact)\b',
    r'^\s*(?:name|patient\s*name|full\s*name|address|age|gender|sex|weight|height|date|time|ref|case|opd|ipd)\s*[:\-]',
    r'\b(?:full\s*name|address|phone\s*number|medical\s*facility|if\s*under\s*\d+)\b',
    r'\b(?:superscription|inscription|subscription|signa|edition|serial\s*number)\b',
    r'\b(?:lot\s*no|lot\s*number|batch\s*no|manufacturer|mfgr|signature|rank\s*and\s*degree|rank\s*&\s*degree)\b',
    r'\b(?:dd\s*form|dd\s*roam|form\s*1289|department\s*of\s*defense|prescription\s*form)\b',
    r'^\s*(?:clinical\s*description|diagnosis|symptoms|history|examination|investigation|rx\s*date|advice|notes)',
    r'^\s*(?:urti|rr\s*-\s*\d+|rs\s*-\s*b/l|bp\s*-\s*\d+|pulse|temp|spo2)\b',
    r'^\s*(?:\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\s*$',
    r'^\s*(?:gu|mic|standard|sr\s*no|sn|ref\s*no)',
]

BULLET_PREFIX_PATTERN = r'^\s*(?:\d+[\.\)]|[\bullet\*\•])\s*'
PRESCRIPTION_PREFIX_PATTERN = r'^\s*(?:Syp\.?|Syrup|Tab\.?|Tablet|Cap\.?|Capsule|Inj\.?|Injection|Oint\.?|Ointment|Drops?|Rx|Take)\b'
DOSAGE_PATTERN = r'\b\d+\s*(?:mg|g|ml|mcg|iu|puffs?|drops?|tsp)\b'
FREQ_PATTERN = r'\b(?:od|qd|bd|bid|tds|tid|qid|hs|sos|prn|stat|weekly|q6h|q8h|1-0-0|1-0-1|1-1-0|1-1-1|1-1-1-1|0-0-1|once|twice|thrice|daily)\b'


def is_non_prescription_section(line: str) -> bool:
    """Filters out non-prescription section headers (doctor credentials, patient details, date, diagnosis)."""
    line_clean = line.strip().lower()
    if not line_clean or len(line_clean) < 2:
        return True

    for pattern in NON_PRESCRIPTION_PATTERNS:
        if re.search(pattern, line_clean, re.IGNORECASE):
            return True

    return False


def extract_candidate_text(line: str) -> str:
    """Strips medical form prefixes and dosage suffixes to isolate candidate drug name."""
    cleaned = re.sub(BULLET_PREFIX_PATTERN, '', line)
    cleaned = re.sub(r'^\s*(?:Syp\.?|Syrup|Tab\.?|Tablet|Cap\.?|Capsule|Inj\.?|Injection|Oint\.?|Ointment|Drops?|Rx)\s+', '', cleaned, flags=re.IGNORECASE)
    match_before_dose = re.search(r'^([A-Za-z0-9\-\.\s]+?)(?=\s*\(\d+|\s+\d+\s*(?:mg|g|ml|mcg|iu|tablets?|caps?|tabs?)|$)', cleaned, flags=re.IGNORECASE)
    if match_before_dose:
        cand = match_before_dose.group(1).strip()
        if len(cand) > 2:
            return cand

    return cleaned.strip()


def group_prescription_lines_into_blocks(text: str) -> List[str]:
    """
    Multi-Line Prescription Block Assembler:
    - Merges continuation lines (dosage, frequency, duration, quantity, indentation) into previous medicine block.
    - Handles bullet points (1., 2., •, -), empty lines, and multi-line dosages.
    """
    raw_lines = text.split('\n')
    blocks: List[str] = []
    current_block: List[str] = []

    db_list = load_medicine_database()

    for line in raw_lines:
        line_str = line.strip()
        if not line_str:
            continue

        if is_non_prescription_section(line_str):
            continue

        line_clean = re.sub(BULLET_PREFIX_PATTERN, '', line_str).strip()
        if not line_clean:
            continue

        is_new_medicine = False

        # 1. Line starts with an explicit form prefix (Tab, Syp, Cap, Inj, Rx) or bullet marker
        if re.search(PRESCRIPTION_PREFIX_PATTERN, line_clean, re.IGNORECASE):
            is_new_medicine = True
        else:
            # 2. Check if candidate matches a known medicine in index (and is not a dosage/duration line)
            cand_name = extract_candidate_text(line_clean)
            is_dosage_or_freq_or_dur = (
                re.search(r'^\d+\s*(?:mg|g|ml|mcg|iu|tablets?|caps?|tabs?|days?|weeks?|months?|d|wk|mth|puffs?|drops?)\b', cand_name, re.IGNORECASE)
                or re.search(r'^\d+-\d+-\d+', cand_name)
                or re.search(FREQ_PATTERN, cand_name, re.IGNORECASE)
            )
            if cand_name and len(cand_name) > 2 and not cand_name.isdigit() and not is_dosage_or_freq_or_dur:
                match_res = match_medicine_rapidfuzz(cand_name)
                if match_res.get("is_known") and match_res.get("similarity_score", 0) >= 85.0:
                    is_new_medicine = True

        # If it's a new medicine header OR no current block exists, start a new block
        if is_new_medicine or not current_block:
            if current_block:
                blocks.append(" ".join(current_block))
            current_block = [line_clean]
        else:
            # Continuation line (dosage on next line, 1-0-1, 5 Days, etc.)
            current_block.append(line_clean)

    if current_block:
        blocks.append(" ".join(current_block))

    return blocks


def parse_ocr_text_to_medicines(text: str, filename: str = "") -> List[ExtractedMedicine]:
    """
    Multi-Line Medicine Knowledge Base Medical Parser:
    - Merges multi-line continuation lines (dosage, frequency, duration) into unified medicine blocks.
    - Handles bullet-style prescriptions, indentation, and empty line delimiters.
    - Word-boundary matching and RapidFuzz fuzzy matching on extracted candidate names.
    - Never fabricates missing values; sets needs_review=True if essential fields are absent.
    """
    medicines: List[ExtractedMedicine] = []
    blocks = group_prescription_lines_into_blocks(text)
    seen_candidates = set()

    for line in blocks:
        # Preprocessing token normalization (e.g. 10mgHS -> 10mg HS, l-0-l -> 1-0-1)
        line = re.sub(r'(\d+\s*(?:mg|g|ml|mcg|iu|tablets?|caps?))([A-Za-z]+)', r'\1 \2', line, flags=re.IGNORECASE)
        line = re.sub(r'\b[lI1]-[0O]-[lI1]\b', '1-0-1', line)

        cand_name_raw = extract_candidate_text(line)
        if not cand_name_raw or len(cand_name_raw) < 2 or cand_name_raw.isdigit():
            continue

        matched_info = match_medicine_rapidfuzz(cand_name_raw)

        # Resolution for matched drug or fallback for valid OCR prescription block
        if matched_info and matched_info.get("is_known"):
            med_name = matched_info["matched_name"]
            drug_obj = matched_info.get("drug_object")
            score = matched_info.get("similarity_score", 75.0)
            is_known = True
        else:
            med_name = cand_name_raw.capitalize()
            drug_obj = None
            score = 70.0
            is_known = False

        cand_key = med_name.lower()
        if cand_key in seen_candidates:
            continue

        seen_candidates.add(cand_key)

        # Extract Raw Dosage
        dosage_match = re.search(r'(\d+\s*(?:mg|g|ml|mcg|iu|puffs?|drops?))', line, re.IGNORECASE)
        raw_dosage = dosage_match.group(1) if dosage_match else ""
        dosage_val = validate_dosage_non_destructive(raw_dosage, drug_obj) if raw_dosage else {"valid": False}

        # Extract Quantity
        qty_match = re.search(r'(\d+)\s*(?:tablets|capsules|pills|tabs|caps|qty|stk|nos)', line, re.IGNORECASE)
        quantity = int(qty_match.group(1)) if qty_match and int(qty_match.group(1)) > 0 else None

        # Extract Frequency
        freq = ""
        freq_conf = 50
        for pattern, expansion in ABBREVIATIONS_MAP.items():
            if re.search(pattern, line, re.IGNORECASE):
                freq = expansion
                freq_conf = 98
                break

        if not freq:
            if re.search(r'\b(twice|2x|b\.i\.d|bid)\b', line, re.IGNORECASE):
                freq = "Twice daily"
                freq_conf = 95
            elif re.search(r'\b(thrice|3x|t\.i\.d|tid)\b', line, re.IGNORECASE):
                freq = "Three times daily"
                freq_conf = 95
            elif re.search(r'\b(once|1x|daily|q6h|q8h)\b', line, re.IGNORECASE):
                freq = "Daily"
                freq_conf = 90

        # Extract Duration
        dur_match = re.search(r'(\d+\s*(?:days|weeks|months|d|wk|mth))', line, re.IGNORECASE)
        duration = dur_match.group(1) if dur_match else ""
        duration_conf = 95 if dur_match else 50

        name_conf = int(score)
        dosage_conf = 95 if dosage_val.get("valid") else 50

        field_conf = FieldConfidence(
            name_confidence=name_conf,
            dosage_confidence=dosage_conf,
            frequency_confidence=freq_conf,
            duration_confidence=duration_conf
        )

        is_missing_fields = not raw_dosage or not freq or not duration
        needs_review = (not is_known) or is_missing_fields or (not dosage_val.get("valid")) or any(c < 80 for c in [name_conf, dosage_conf, freq_conf, duration_conf])
        overall_conf = round((name_conf + dosage_conf + freq_conf + duration_conf) / 400.0, 2)

        medicines.append(
            ExtractedMedicine(
                medicine_name=med_name,
                dosage=raw_dosage,
                quantity=quantity,
                frequency=freq,
                duration=duration,
                confidence=overall_conf,
                field_confidence=field_conf,
                needs_review=needs_review
            )
        )

    return medicines
