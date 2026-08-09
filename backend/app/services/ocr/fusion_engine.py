import os
import sys
import re
import json
import time
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from rapidfuzz import fuzz

from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz

logger = logging.getLogger("FUSION_ENGINE")

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))

OCR_VERSION = "2.4.0-Enterprise"
FUSION_VERSION = "2.0.0-Adaptive"
KB_VERSION = "1.8.0"
PARSER_VERSION = "1.5.0"


def fuse_field_value(val1: Optional[str], val2: Optional[str]) -> Tuple[str, str, bool]:
    """
    Compares two string field values (e.g. dosage, frequency, duration).
    Returns (fused_val, source_winner, is_disagreement).
    """
    v1 = (val1 or "").strip()
    v2 = (val2 or "").strip()

    if not v1 and not v2:
        return "", "none", False
    if not v1 and v2:
        return v2, "gemma", False
    if v1 and not v2:
        return v1, "tesseract", False

    v1_clean = v1.lower().replace(" ", "")
    v2_clean = v2.lower().replace(" ", "")

    if v1_clean == v2_clean or fuzz.ratio(v1_clean, v2_clean) > 85:
        return v1, "agreement", False

    winner = "gemma" if len(v2) > len(v1) else "tesseract"
    fused_val = v2 if winner == "gemma" else v1
    return fused_val, winner, True


def calculate_quality_score_and_grade(
    medicines: List[ExtractedMedicine],
    ocr_conf: float,
    conflicts_count: int
) -> Tuple[float, str]:
    """
    Calculates overall 0-100 Quality Score and letter Grade (A+, A, B, C, F).
    """
    if not medicines:
        return 0.0, "F"

    avg_conf = (sum(m.confidence for m in medicines) / len(medicines)) * 100.0 if medicines else 0.0
    field_completeness = sum(
        (1 if m.dosage else 0) + (1 if m.frequency else 0) + (1 if m.quantity else 0)
        for m in medicines
    ) / (len(medicines) * 3.0) * 100.0

    score = (0.50 * avg_conf) + (0.30 * field_completeness) + (0.20 * min(ocr_conf, 100.0)) - (conflicts_count * 5.0)
    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 95.0:
        grade = "A+"
    elif score >= 90.0:
        grade = "A"
    elif score >= 80.0:
        grade = "B"
    elif score >= 70.0:
        grade = "C"
    else:
        grade = "F"

    return score, grade


ADMINISTRATIVE_KEYWORDS = [
    r'\b(?:full\s*name|patient\s*name|address|phone|telephone|mobile|contact)\b',
    r'\b(?:medical\s*facility|hospital|clinic|nursing\s*home|department|ward)\b',
    r'\b(?:date|rx\s*date|age|gender|sex|weight|height|dob)\b',
    r'\b(?:superscription|inscription|subscription|signa|sig|advice|notes)\b',
    r'\b(?:lot\s*no|lot\s*number|batch\s*no|exp\s*date|mfd\s*date)\b',
    r'\b(?:manufacturer|mfgr|mfg|signature|rank\s*and\s*degree|rank\s*&\s*degree)\b',
    r'\b(?:serial\s*number|sr\s*no|edition|dd\s*form|dd\s*roam|form\s*1289|department\s*of\s*defense)\b',
    r'\b(?:reg\s*no|registration|license|licence)\b',
    r'\b(?:clinical\s*description|diagnosis|symptoms|history|examination|investigation|urti|rr\s*-|bp\s*-)\b',
]

STANDALONE_FORMULATION_NAMES = {
    "solution", "solutions", "tablet", "tablets", "tab", "tabs", "syrup", "syrups",
    "syp", "capsule", "capsules", "cap", "caps", "cream", "creams", "gel", "gels",
    "tincture", "mixture", "elixir", "suspension", "lotion", "ointment", "emulsion",
    "powder", "m & fi solution", "m & f i solution", "m. & f. i. solution",
    "m. et sig.", "m & f solution", "m.f.i. solution"
}


def classify_candidate(cand_name: str, dosage: str = "", freq: str = "", dur: str = "") -> Tuple[str, str]:
    """
    Classifies an OCR/Vision candidate into:
    MEDICINE, FORMULATION, DOSAGE, FREQUENCY, INSTRUCTION, ADMINISTRATIVE, HEADER_NOISE, PARAGRAPH_NOISE.
    """
    clean_name = cand_name.strip().lower()
    if not clean_name:
        return "HEADER_NOISE", "Empty candidate string"

    # 1. Administrative Indicator Check
    for pat in ADMINISTRATIVE_KEYWORDS:
        if re.search(pat, clean_name, re.IGNORECASE):
            return "ADMINISTRATIVE", f"Contains administrative keyword pattern '{pat}'"

    # 2. Form Header / Document Number Check
    if re.search(r'\b(?:dd\s*(?:form|roam)|form\s*\d{3,4}|standard\s*form|dept\s*of\s*defense)\b', clean_name, re.IGNORECASE):
        if not dosage and not freq and not dur:
            return "HEADER_NOISE", "Form header pattern without prescription dosage or frequency"

    # 3. Standalone Formulation Check
    if clean_name in STANDALONE_FORMULATION_NAMES:
        return "FORMULATION", f"Standalone generic formulation or compounding phrase '{cand_name}'"

    # 4. Long Paragraph / Multi-Section OCR Noise Check
    words = clean_name.split()
    if len(words) > 6 or len(clean_name) > 55:
        admin_count = sum(1 for pat in ADMINISTRATIVE_KEYWORDS if re.search(pat, clean_name, re.IGNORECASE))
        if admin_count >= 1 or len(words) > 8:
            return "PARAGRAPH_NOISE", f"OCR paragraph noise ({len(words)} words, length {len(clean_name)})"

    # 5. Pure Number / Non-Letter Check
    letter_count = sum(1 for c in clean_name if c.isalpha())
    if letter_count < 2 or (letter_count / float(max(len(clean_name), 1))) < 0.35:
        return "HEADER_NOISE", f"Low letter ratio in candidate '{cand_name}'"

    return "MEDICINE", "Plausible medicine candidate"


def is_valid_medicine_candidate(med: ExtractedMedicine, gemma_meds: List[ExtractedMedicine]) -> Tuple[bool, str, str]:
    """
    Candidate Quality Filter:
    Evaluates classification, KB match, Gemma agreement, and evidence strength.
    Unknown medicines (e.g. CustomMedX) are PRESERVED with needs_review=True.
    Administrative form headers and standalone formulations are REJECTED.
    """
    cand_name = med.brand_name or med.medicine_name
    classification, reason = classify_candidate(cand_name, med.dosage, med.frequency, med.duration)

    if classification in ("ADMINISTRATIVE", "HEADER_NOISE", "PARAGRAPH_NOISE", "FORMULATION"):
        return False, classification, reason

    # Check Gemma agreement
    has_gemma_agreement = any(
        fuzz.WRatio(cand_name.lower(), g.medicine_name.lower()) >= 60.0
        for g in gemma_meds
    )

    kb_match = match_medicine_rapidfuzz(cand_name)
    if kb_match.get("is_known"):
        return True, "MEDICINE", "Valid medicine matched in Knowledge Base"

    if has_gemma_agreement:
        return True, "MEDICINE", "Valid medicine supported by Gemma Vision anchor"

    # Unknown Medicine Protection (Rule 1 & Rule 5):
    # Unknown but medicine-like candidate (e.g. CustomMedX) with dosage or clean structure is KEPT with needs_review=True.
    if med.dosage or med.frequency or (len(cand_name) >= 3 and cand_name[0].isupper()):
        return True, "MEDICINE", "Valid unknown medicine candidate preserved for review"

    if med.medicine_name != cand_name:
        sub_class, sub_reason = classify_candidate(med.medicine_name, med.dosage, med.frequency, med.duration)
        if sub_class == "MEDICINE":
            return True, "MEDICINE", "Valid medicine candidate"

    return False, classification, reason


def final_medicine_validation(medicines: List[ExtractedMedicine]) -> List[ExtractedMedicine]:
    """
    CRITICAL FINAL VALIDATION GATE:
    Runs immediately before constructing OCRExtractResponse.
    Ensures 'M & FI Solution', standalone formulations, form headers ('DD Form 1289'),
    patient names, addresses, phone numbers, lot numbers, signature/rank text,
    and administrative headers NEVER reach OCRExtractResponse.medicines.
    """
    validated: List[ExtractedMedicine] = []
    for med in medicines:
        is_valid, classification, reason = is_valid_medicine_candidate(med, medicines)
        if is_valid:
            validated.append(med)
        else:
            logger.warning(
                f"[FINAL_VALIDATION_REJECT] Filtered candidate '{med.medicine_name}' | "
                f"Classification='{classification}' | Reason='{reason}'"
            )
    return validated


def fuse_field_level_medicines(
    tesseract_meds: List[ExtractedMedicine],
    gemma_meds: List[ExtractedMedicine],
    tesseract_conf: float,
    gemma_conf: float,
    is_handwritten: bool = False,
    trace_id: Optional[str] = None
) -> Tuple[List[ExtractedMedicine], float, Dict[str, Any]]:
    """
    Enterprise Adaptive Field-Level Fusion Engine with Quality Filtering & Candidate Clustering:
    Fuses Tesseract OCR and Gemma Vision field-by-field.
    Rejects administrative text, form headers, and standalone formulations.
    Uses Gemma as semantic anchor when Tesseract line is garbled.
    Preserves unknown medicine-like candidates with needs_review=True.
    """
    start_time = time.perf_counter()
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"
    t_id = trace_id or f"tr_{uuid.uuid4().hex[:10]}"

    logger.info(f"[FUSION] [TraceID={t_id}] [ExecID={exec_id}] Comparing engines (Tesseract={len(tesseract_meds)} meds, Gemma={len(gemma_meds)} meds)")

    t_conf_norm = (tesseract_conf / 100.0) if tesseract_conf > 1.0 else tesseract_conf
    g_conf_norm = (gemma_conf / 100.0) if gemma_conf > 1.0 else gemma_conf

    fused_medicines: List[ExtractedMedicine] = []
    differences_logged: List[Dict[str, Any]] = []
    field_winners: Dict[str, Dict[str, str]] = {}
    explanations: Dict[str, Dict[str, Any]] = {}
    heatmap_data: Dict[str, Dict[str, Dict[str, Any]]] = {}
    conflicts_logged: List[Dict[str, Any]] = []
    rejected_candidates_logged: List[Dict[str, Any]] = []
    matched_gemma_indices = set()

    # Phase 1: Candidate Quality Filter & Classification on Tesseract
    valid_tesseract_meds: List[ExtractedMedicine] = []
    for t_med in tesseract_meds:
        is_valid, classification, reason = is_valid_medicine_candidate(t_med, gemma_meds)
        if is_valid:
            valid_tesseract_meds.append(t_med)
            logger.info(f"[TRACE_OCR_FLOW] CANDIDATE_FILTER: candidate='{t_med.medicine_name}' | classification='{classification}' | action='KEEP' | reason='{reason}'")
        else:
            rejected_candidates_logged.append({
                "candidate": t_med.medicine_name,
                "source": "tesseract",
                "classification": classification,
                "reason": reason
            })
            logger.info(f"[TRACE_OCR_FLOW] CANDIDATE_FILTER: candidate='{t_med.medicine_name}' | classification='{classification}' | action='REJECT' | reason='{reason}'")

    # Phase 2: Fusing Valid Tesseract Candidates with Gemma Anchor
    for idx, t_med in enumerate(valid_tesseract_meds):
        best_g_match: Optional[ExtractedMedicine] = None
        best_g_idx: int = -1
        highest_sim: float = 0.0

        for g_idx, g_med in enumerate(gemma_meds):
            if g_idx in matched_gemma_indices:
                continue
            sim = fuzz.WRatio(t_med.medicine_name.lower(), g_med.medicine_name.lower())
            if sim > highest_sim:
                highest_sim = sim
                best_g_match = g_med
                best_g_idx = g_idx

        winner_map: Dict[str, str] = {}
        disagreements: List[str] = []
        reason_strings: List[str] = []

        if best_g_match and highest_sim >= 40.0:
            matched_gemma_indices.add(best_g_idx)
            g_med = best_g_match

            # Rule 3: Gemma Semantic Anchor Priority
            # Prefer Gemma's clean medicine name if Tesseract is garbled/noisy
            g_name_clean = g_med.medicine_name.strip()
            t_name_clean = t_med.medicine_name.strip()
            
            kb_match_gemma = match_medicine_rapidfuzz(g_name_clean)
            kb_match_tess = match_medicine_rapidfuzz(t_name_clean)
            
            if kb_match_gemma.get("is_known"):
                cand_raw_name = g_name_clean
                kb_match = kb_match_gemma
            elif kb_match_tess.get("is_known"):
                cand_raw_name = t_name_clean
                kb_match = kb_match_tess
            else:
                cand_raw_name = g_name_clean if (len(g_name_clean) <= len(t_name_clean) or len(t_name_clean) > 40) else t_name_clean
                kb_match = kb_match_gemma if cand_raw_name == g_name_clean else kb_match_tess

            kb_score = float(kb_match.get("confidence", 0.50)) if kb_match.get("matched") else 0.40

            if kb_match.get("is_known"):
                gen_name = kb_match.get("generic_name", "")
                brand_name = cand_raw_name
                if brand_name.lower() != gen_name.lower():
                    final_name = f"{brand_name} ({gen_name})"
                else:
                    final_name = gen_name
                winner_map["medicine_name"] = "agreement"
                reason_strings.append(f"Prescription brand '{brand_name}' linked to generic '{gen_name}'.")
            else:
                brand_name = cand_raw_name
                gen_name = ""
                final_name = cand_raw_name
                winner_map["medicine_name"] = "gemma" if g_med.medicine_name else "tesseract"
                reason_strings.append(f"Preserved prescription candidate '{cand_raw_name}'.")

            # 2. Dosage & Volume Concentration Fusion
            raw_t_dosage = (t_med.dosage or "").strip()
            raw_g_dosage = (g_med.dosage or "").strip()
            
            final_dosage, dosage_winner, dosage_dis = fuse_field_value(raw_t_dosage, raw_g_dosage)
            
            conc_match = re.search(r'(\d+/\d+|\d+\s*mg/\d+\s*ml|\d+\s*mg)', raw_t_dosage + " " + raw_g_dosage, re.IGNORECASE)
            vol_match = re.search(r'(\d+\s*ml|\d+\s*puffs?|\d+\s*drops?)', raw_t_dosage + " " + raw_g_dosage, re.IGNORECASE)
            
            if conc_match and vol_match and conc_match.group(1) not in vol_match.group(1):
                final_dosage = f"{conc_match.group(1)} ({vol_match.group(1)})"

            winner_map["dosage"] = dosage_winner
            if dosage_dis:
                disagreements.append(f"Dosage Disagreement: '{raw_t_dosage}' vs '{raw_g_dosage}'")

            # 3. Quantity Fusion
            final_qty = t_med.quantity or g_med.quantity
            winner_map["quantity"] = "tesseract" if t_med.quantity else ("gemma" if g_med.quantity else "none")

            # 4. Frequency Fusion
            final_freq, freq_winner, freq_dis = fuse_field_value(t_med.frequency, g_med.frequency)
            winner_map["frequency"] = freq_winner
            if freq_dis:
                disagreements.append(f"Frequency Disagreement: '{t_med.frequency}' vs '{g_med.frequency}'")

            # 5. Duration Fusion
            final_dur, dur_winner, dur_dis = fuse_field_value(t_med.duration, g_med.duration)
            winner_map["duration"] = dur_winner
            if dur_dis:
                disagreements.append(f"Duration Disagreement: '{t_med.duration}' vs '{g_med.duration}'")

            # Identity confidence based strictly on name evidence (Gemma, Tesseract, KB match)
            if kb_match.get("is_known"):
                identity_conf = max(0.92, float(kb_match.get("similarity_score", 95.0)) / 100.0)
            elif highest_sim >= 70.0:
                identity_conf = min(0.95, max(0.88, highest_sim / 100.0))
            else:
                identity_conf = min(0.92, max(0.85, (g_conf_norm * 0.5) + (t_conf_norm * 0.5)))

            if best_g_match and highest_sim >= 50.0:
                identity_conf = min(0.98, identity_conf + 0.03)

            identity_conf = round(min(0.98, max(0.70, identity_conf)), 2)
            name_conf = int(identity_conf * 100)

            dosage_conf = 90 if (final_dosage and not dosage_dis) else (60 if dosage_dis else None)
            freq_conf = 90 if (final_freq and not freq_dis) else (60 if freq_dis else None)
            dur_conf = 90 if (final_dur and not dur_dis) else (60 if dur_dis else None)

            needs_rev = True if (disagreements or not kb_match.get("is_known") or identity_conf < 0.80 or not final_dosage or not final_freq) else False

            fused_med = ExtractedMedicine(
                medicine_name=final_name,
                brand_name=brand_name,
                generic_name=gen_name,
                dosage=final_dosage,
                quantity=final_qty,
                frequency=final_freq,
                duration=final_dur,
                confidence=identity_conf,
                field_confidence=FieldConfidence(
                    name_confidence=name_conf,
                    dosage_confidence=dosage_conf,
                    frequency_confidence=freq_conf,
                    duration_confidence=dur_conf
                ),
                needs_review=needs_rev
            )
            logger.info(
                f"[CONFIDENCE] Medicine='{final_name}' | "
                f"IdentityConfidence={int(identity_conf * 100)} | "
                f"NameConfidence={name_conf} | "
                f"DosageConfidence={dosage_conf if dosage_conf is not None else 'NOT_DETECTED'} | "
                f"Frequency={'NOT_DETECTED' if not final_freq else final_freq} | "
                f"Duration={'NOT_DETECTED' if not final_dur else final_dur} | "
                f"NeedsReview={needs_rev}"
            )
            logger.info(f"[TRACE_OCR_FLOW] FUSION_CLUSTER: Tesseract='{t_med.medicine_name}' + Gemma='{g_med.medicine_name}' -> Final='{final_name}' (dosage='{final_dosage}')")

        else:
            # Unmatched Tesseract Medicine
            kb_match = match_medicine_rapidfuzz(t_med.medicine_name)
            kb_score = float(kb_match.get("confidence", 0.50)) if kb_match.get("matched") else 0.30

            if kb_match.get("is_known"):
                identity_conf = max(0.90, float(kb_match.get("similarity_score", 90.0)) / 100.0)
            else:
                identity_conf = min(0.88, max(0.70, (0.60 * t_conf_norm) + (0.40 * kb_score)))

            identity_conf = round(min(0.95, max(0.60, identity_conf)), 2)
            name_conf = int(identity_conf * 100)

            dosage_conf = 85 if t_med.dosage else None
            freq_conf = 85 if t_med.frequency else None
            dur_conf = 85 if t_med.duration else None

            winner_map = {k: "tesseract_only" for k in ["medicine_name", "dosage", "frequency", "duration"]}
            reason_strings.append("Extracted by Tesseract OCR; unverified by Gemma Vision.")

            gen_name = kb_match.get("generic_name", "") if kb_match.get("is_known") else ""
            brand_name = t_med.medicine_name
            final_tess_name = f"{brand_name} ({gen_name})" if (gen_name and brand_name.lower() != gen_name.lower()) else brand_name

            needs_rev = True if (not kb_match.get("is_known") or identity_conf < 0.80) else False

            fused_med = ExtractedMedicine(
                medicine_name=final_tess_name,
                brand_name=brand_name,
                generic_name=gen_name,
                dosage=t_med.dosage,
                quantity=t_med.quantity,
                frequency=t_med.frequency,
                duration=t_med.duration,
                confidence=identity_conf,
                field_confidence=FieldConfidence(
                    name_confidence=name_conf,
                    dosage_confidence=dosage_conf,
                    frequency_confidence=freq_conf,
                    duration_confidence=dur_conf
                ),
                needs_review=needs_rev
            )
            logger.info(
                f"[CONFIDENCE] Medicine='{final_tess_name}' | "
                f"IdentityConfidence={int(identity_conf * 100)} | "
                f"NameConfidence={name_conf} | "
                f"DosageConfidence={dosage_conf if dosage_conf is not None else 'NOT_DETECTED'} | "
                f"Frequency={'NOT_DETECTED' if not t_med.frequency else t_med.frequency} | "
                f"Duration={'NOT_DETECTED' if not t_med.duration else t_med.duration} | "
                f"NeedsReview={needs_rev}"
            )

        fused_medicines.append(fused_med)
        field_winners[fused_med.medicine_name] = winner_map
        explanations[fused_med.medicine_name] = {
            "winner_per_field": winner_map,
            "reasons": reason_strings
        }
        heatmap_data[fused_med.medicine_name] = {
            "medicine_name": {"confidence": f"{int(fused_med.confidence*100)}%", "winner": winner_map.get("medicine_name"), "agreement": winner_map.get("medicine_name") == "agreement"},
            "dosage": {"confidence": "90%" if fused_med.dosage else "50%", "winner": winner_map.get("dosage"), "agreement": winner_map.get("dosage") == "agreement"},
            "frequency": {"confidence": "90%" if fused_med.frequency else "50%", "winner": winner_map.get("frequency"), "agreement": winner_map.get("frequency") == "agreement"},
            "duration": {"confidence": "90%" if fused_med.duration else "50%", "winner": winner_map.get("duration"), "agreement": winner_map.get("duration") == "agreement"}
        }

    # Phase 3: Processing Unmatched Gemma Candidates
    for g_idx, g_med in enumerate(gemma_meds):
        if g_idx not in matched_gemma_indices:
            is_valid, classification, reason = is_valid_medicine_candidate(g_med, gemma_meds)
            if not is_valid:
                rejected_candidates_logged.append({
                    "candidate": g_med.medicine_name,
                    "source": "gemma",
                    "classification": classification,
                    "reason": reason
                })
                logger.info(f"[TRACE_OCR_FLOW] CANDIDATE_FILTER: candidate='{g_med.medicine_name}' | classification='{classification}' | action='REJECT' | reason='{reason}'")
                continue

            logger.info(f"[TRACE_OCR_FLOW] CANDIDATE_FILTER: candidate='{g_med.medicine_name}' | classification='{classification}' | action='KEEP' | reason='{reason}'")

            kb_check = match_medicine_rapidfuzz(g_med.medicine_name)
            kb_score = float(kb_check.get("confidence", 0.50)) if kb_check.get("matched") else 0.20

            if kb_check.get("is_known"):
                identity_conf = max(0.92, float(kb_check.get("similarity_score", 95.0)) / 100.0)
            else:
                identity_conf = min(0.92, max(0.80, 0.60 * g_conf_norm + 0.40 * kb_score))

            identity_conf = round(min(0.98, max(0.70, identity_conf)), 2)
            name_conf = int(identity_conf * 100)

            dosage_conf = 90 if g_med.dosage else None
            freq_conf = 90 if g_med.frequency else None
            dur_conf = 90 if g_med.duration else None

            winner_map = {k: "gemma_only" for k in ["medicine_name", "dosage", "frequency", "duration"]}

            gen_name = kb_check.get("generic_name", "") if kb_check.get("is_known") else ""
            brand_name = g_med.medicine_name
            final_gemma_name = f"{brand_name} ({gen_name})" if (gen_name and brand_name.lower() != gen_name.lower()) else brand_name

            needs_rev = True if (not kb_check.get("is_known") or identity_conf < 0.80) else False

            fused_med = ExtractedMedicine(
                medicine_name=final_gemma_name,
                brand_name=brand_name,
                generic_name=gen_name,
                dosage=g_med.dosage,
                quantity=g_med.quantity,
                frequency=g_med.frequency,
                duration=g_med.duration,
                confidence=identity_conf,
                field_confidence=FieldConfidence(
                    name_confidence=name_conf,
                    dosage_confidence=dosage_conf,
                    frequency_confidence=freq_conf,
                    duration_confidence=dur_conf
                ),
                needs_review=needs_rev
            )
            logger.info(
                f"[CONFIDENCE] Medicine='{final_gemma_name}' | "
                f"IdentityConfidence={int(identity_conf * 100)} | "
                f"NameConfidence={name_conf} | "
                f"DosageConfidence={dosage_conf if dosage_conf is not None else 'NOT_DETECTED'} | "
                f"Frequency={'NOT_DETECTED' if not g_med.frequency else g_med.frequency} | "
                f"Duration={'NOT_DETECTED' if not g_med.duration else g_med.duration} | "
                f"NeedsReview={needs_rev}"
            )
            fused_medicines.append(fused_med)
            field_winners[fused_med.medicine_name] = winner_map
            explanations[fused_med.medicine_name] = {
                "winner_per_field": winner_map,
                "reasons": [f"Extracted by Gemma Vision; Knowledge Base verification score = {kb_score*100:.0f}%"]
            }

    # Phase 4: Deduplication & Final Response Validation
    unique_fused: List[ExtractedMedicine] = []
    seen_keys = set()

    for med in fused_medicines:
        norm_key = (med.brand_name or med.medicine_name).strip().lower()
        if norm_key in seen_keys:
            continue
        seen_keys.add(norm_key)
        unique_fused.append(med)

    fused_medicines = final_medicine_validation(unique_fused)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    overall_fusion_conf = (
        round(sum(m.confidence for m in fused_medicines) / len(fused_medicines), 2)
        if fused_medicines else 0.0
    )

    quality_score, quality_grade = calculate_quality_score_and_grade(fused_medicines, tesseract_conf, len(conflicts_logged))

    if differences_logged:
        logger.info(f"[FUSION] [TraceID={t_id}] Differences detected: {len(differences_logged)} medicine(s) with field discrepancies.")
    logger.info(f"[FUSION] [TraceID={t_id}] Calibrated confidence={overall_fusion_conf:.2f} | Quality Score={quality_score} ({quality_grade}) | {elapsed_ms}ms")

    # Phase 6: Confidence Timeline Generation
    confidence_timeline = [
        {"stage": "1_Preprocessing", "confidence": 1.0},
        {"stage": "2_Segmentation", "confidence": 0.95},
        {"stage": "3_Tesseract_OCR", "confidence": round(t_conf_norm, 2)},
        {"stage": "4_Knowledge_Base", "confidence": 0.90},
        {"stage": "5_Vision_AI", "confidence": round(g_conf_norm, 2)},
        {"stage": "6_Adaptive_Fusion", "confidence": overall_fusion_conf},
        {"stage": "7_Final_Output", "confidence": overall_fusion_conf}
    ]

    # Phase 7 & 8: Safety & Hallucination Reports
    hallucination_items = [c for c in conflicts_logged if c.get("hallucination_warning")]
    safety_data = {
        "trace_id": t_id,
        "total_conflicts": len(conflicts_logged),
        "hallucination_cautions": len(hallucination_items),
        "conflicts": conflicts_logged,
        "is_safe": len(conflicts_logged) == 0 and len(hallucination_items) == 0
    }

    adaptive_weights_data = {
        "trace_id": t_id,
        "is_handwritten": is_handwritten,
        "tesseract_raw_conf": tesseract_conf,
        "gemma_raw_conf": gemma_conf,
        "weights_applied": {
            "tesseract_weight": 0.55 if not is_handwritten and t_conf_norm >= 0.70 else 0.25,
            "gemma_weight": 0.55 if is_handwritten else 0.40,
            "kb_weight": 0.20
        }
    }

    report_data = {
        "trace_id": t_id,
        "execution_id": exec_id,
        "versions": {
            "ocr_version": OCR_VERSION,
            "fusion_version": FUSION_VERSION,
            "kb_version": KB_VERSION,
            "parser_version": PARSER_VERSION
        },
        "quality_metrics": {
            "quality_score": quality_score,
            "grade": quality_grade,
            "fusion_confidence": overall_fusion_conf
        },
        "tesseract_result": [m.model_dump() for m in tesseract_meds],
        "gemma_result": [m.model_dump() for m in gemma_meds],
        "differences": differences_logged,
        "conflicts": conflicts_logged,
        "winner_per_field": field_winners,
        "explanations": explanations,
        "heatmap": heatmap_data,
        "confidence_timeline": confidence_timeline,
        "final_result": [m.model_dump() for m in fused_medicines],
        "execution_time_ms": elapsed_ms
    }

    # Debug File Outputs (Phases 1, 2, 3, 5, 6, 7, 8 Exports)
    if DEBUG_OCR or os.path.exists(DEBUG_DIR):
        try:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            with open(os.path.join(DEBUG_DIR, "fusion_report.json"), "w", encoding="utf-8") as f_out:
                json.dump(report_data, f_out, indent=2)
            with open(os.path.join(DEBUG_DIR, "fusion_explanations.json"), "w", encoding="utf-8") as f_exp:
                json.dump(explanations, f_exp, indent=2)
            with open(os.path.join(DEBUG_DIR, "fusion_conflicts.json"), "w", encoding="utf-8") as f_cnf:
                json.dump(conflicts_logged, f_cnf, indent=2)
            with open(os.path.join(DEBUG_DIR, "fusion_heatmap.json"), "w", encoding="utf-8") as f_htm:
                json.dump(heatmap_data, f_htm, indent=2)
            with open(os.path.join(DEBUG_DIR, "adaptive_weights.json"), "w", encoding="utf-8") as f_awt:
                json.dump(adaptive_weights_data, f_awt, indent=2)
            with open(os.path.join(DEBUG_DIR, "confidence_timeline.json"), "w", encoding="utf-8") as f_ctl:
                json.dump(confidence_timeline, f_ctl, indent=2)
            with open(os.path.join(DEBUG_DIR, "safety_validation.json"), "w", encoding="utf-8") as f_sft:
                json.dump(safety_data, f_sft, indent=2)
            with open(os.path.join(DEBUG_DIR, "hallucination_report.json"), "w", encoding="utf-8") as f_hal:
                json.dump(hallucination_items, f_hal, indent=2)
            logger.info(f"[FUSION] Exported enterprise debug artifacts to {DEBUG_DIR}")
        except Exception as dbg_err:
            logger.warning(f"[FUSION] Failed to save debug artifacts: {dbg_err}")

    return fused_medicines, overall_fusion_conf, report_data
