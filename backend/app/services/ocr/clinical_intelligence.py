import os
import re
import time
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine

logger = logging.getLogger("CLINICAL_INTELLIGENCE")

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))

# Knowledge maps for clinical checks
GENERIC_ALIASES_MAP = {
    "calpol": "Paracetamol",
    "dolo": "Paracetamol",
    "crocin": "Paracetamol",
    "meftal": "Mefenamic Acid",
    "pantop": "Pantoprazole",
    "pan": "Pantoprazole",
    "pantocid": "Pantoprazole",
    "rabeprazole": "Rabeprazole",
    "razo": "Rabeprazole",
    "amoxicillin": "Amoxicillin",
    "augmentin": "Amoxicillin + Clavulanic Acid",
    "azithromycin": "Azithromycin",
    "azithral": "Azithromycin",
    "levosalbutamol": "Levosalbutamol",
    "levolin": "Levosalbutamol",
    "cetirizine": "Cetirizine",
    "cetzine": "Cetirizine",
    "telmisartan": "Telmisartan",
    "telma": "Telmisartan",
}

THERAPEUTIC_CLASS_MAP = {
    "pantoprazole": "Proton Pump Inhibitor (PPI)",
    "rabeprazole": "Proton Pump Inhibitor (PPI)",
    "omeprazole": "Proton Pump Inhibitor (PPI)",
    "lansoprazole": "Proton Pump Inhibitor (PPI)",
    "paracetamol": "Analgesic / Antipyretic",
    "mefenamic acid": "NSAID",
    "ibuprofen": "NSAID",
    "aceclofenac": "NSAID",
    "diclofenac": "NSAID",
    "cetirizine": "Antihistamine",
    "levocetirizine": "Antihistamine",
    "amoxicillin": "Antibiotic (Penicillin)",
    "azithromycin": "Antibiotic (Macrolide)",
    "ciprofloxacin": "Antibiotic (Fluoroquinolone)",
}

KNOWN_INTERACTIONS = [
    ({"paracetamol", "mefenamic acid"}, "Co-administration of Paracetamol and Mefenamic Acid increases risk of gastric toxicity."),
    ({"pantoprazole", "rabeprazole"}, "Duplicate PPI therapy (Pantoprazole + Rabeprazole) is redundant."),
    ({"aspirin", "warfarin"}, "High bleeding risk: Aspirin + Warfarin co-administration."),
    ({"ciprofloxacin", "theophylline"}, "Increased theophylline toxicity when taken with Ciprofloxacin.")
]

MAX_SINGLE_DOSE_MG = {
    "paracetamol": 1000,
    "pantoprazole": 80,
    "rabeprazole": 40,
    "amoxicillin": 1000,
    "azithromycin": 500,
    "cetirizine": 20,
    "mefenamic acid": 500,
    "aceclofenac": 200,
}


def validate_prescription_clinically(
    medicines: List[ExtractedMedicine],
    ocr_conf: float = 95.0,
    debug: bool = False,
    debug_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clinical Intelligence Layer:
    Performs clinical safety validation and annotations without modifying original OCR results.
    Execution latency strictly < 10 ms.
    """
    start_time = time.perf_counter()

    if debug_dir is None:
        debug_dir = DEBUG_DIR

    is_debug = debug or DEBUG_OCR

    warnings: List[Dict[str, str]] = []
    seen_names: List[str] = []
    seen_generics: set = set()
    seen_classes: Dict[str, str] = {}

    for med in medicines:
        m_name = med.medicine_name.strip() if med.medicine_name else ""
        m_name_lower = m_name.lower()

        # 1. Unknown / Unrecognized Medicine
        if not m_name or m_name_lower in ["unknown", "unrecognized"] or med.needs_review:
            warnings.append({
                "type": "unknown_medicine",
                "medicine": m_name or "Unknown",
                "message": "Medicine unlisted or unreadable; manual clinical review required.",
                "severity": "high"
            })
            if not m_name:
                continue

        # 2. Repeated Medicine Check
        if m_name_lower in [x.lower() for x in seen_names]:
            warnings.append({
                "type": "repeated_medicine",
                "medicine": m_name,
                "message": f"Medicine '{m_name}' is prescribed multiple times in the same prescription.",
                "severity": "medium"
            })
        seen_names.append(m_name)

        generic_name = GENERIC_ALIASES_MAP.get(m_name_lower, m_name)
        generic_lower = generic_name.lower()

        # 3. Duplicate Generic Check
        if generic_lower in seen_generics and m_name_lower not in [x.lower() for x in seen_names[:-1]]:
            warnings.append({
                "type": "duplicate_generic",
                "medicine": m_name,
                "message": f"Same generic medicine ('{generic_name}') already prescribed under another brand.",
                "severity": "high"
            })
        seen_generics.add(generic_lower)

        # 4. Duplicate Therapy Class Check
        t_class = THERAPEUTIC_CLASS_MAP.get(generic_lower)
        if t_class:
            if t_class in seen_classes:
                prev_med = seen_classes[t_class]
                if prev_med.lower() != m_name_lower:
                    warnings.append({
                        "type": "duplicate_therapy",
                        "medicine": m_name,
                        "message": f"Duplicate therapeutic class ({t_class}) prescribed alongside '{prev_med}'.",
                        "severity": "medium"
                    })
            else:
                seen_classes[t_class] = m_name

        # 5. Dosage Validation (Missing / High / Impossible)
        dosage_str = med.dosage or ""
        if not dosage_str.strip():
            warnings.append({
                "type": "missing_dosage",
                "medicine": m_name,
                "message": f"Dosage missing for '{m_name}'.",
                "severity": "low"
            })
        else:
            dose_match = re.search(r'(\d+)\s*(?:mg|g)', dosage_str, re.IGNORECASE)
            if dose_match:
                val = int(dose_match.group(1))
                if 'g' in dosage_str.lower() and 'mg' not in dosage_str.lower():
                    val *= 1000

                if val >= 5000:
                    warnings.append({
                        "type": "impossible_dosage",
                        "medicine": m_name,
                        "message": f"Dosage '{dosage_str}' for '{m_name}' is clinically impossible or extreme.",
                        "severity": "high"
                    })
                elif generic_lower in MAX_SINGLE_DOSE_MG and val > MAX_SINGLE_DOSE_MG[generic_lower]:
                    warnings.append({
                        "type": "high_dosage",
                        "medicine": m_name,
                        "message": f"Dosage '{dosage_str}' for '{m_name}' exceeds typical single dose maximum ({MAX_SINGLE_DOSE_MG[generic_lower]}mg).",
                        "severity": "high"
                    })

        # 6. Missing Frequency Check
        if not med.frequency or not med.frequency.strip():
            warnings.append({
                "type": "missing_frequency",
                "medicine": m_name,
                "message": f"Frequency missing for '{m_name}'.",
                "severity": "low"
            })

        # 7. Missing Duration Check
        if not med.duration or not med.duration.strip():
            warnings.append({
                "type": "missing_duration",
                "medicine": m_name,
                "message": f"Duration missing for '{m_name}'.",
                "severity": "low"
            })

        # 8. Suspicious / Low Confidence OCR
        if med.confidence < 0.75 or (med.field_confidence and med.field_confidence.name_confidence < 70):
            warnings.append({
                "type": "suspicious_ocr",
                "medicine": m_name,
                "message": f"Low OCR confidence ({med.confidence*100:.1f}%) for '{m_name}'; manual review recommended.",
                "severity": "medium"
            })

    # 9. Drug Interaction Lookup
    for interaction_set, inter_msg in KNOWN_INTERACTIONS:
        if interaction_set.issubset(seen_generics):
            warnings.append({
                "type": "drug_interaction",
                "medicine": " + ".join(sorted(interaction_set)),
                "message": inter_msg,
                "severity": "high"
            })

    needs_review = any(w["severity"] in ["high", "medium"] for w in warnings) or (ocr_conf < 80.0)
    is_safe = not any(w["severity"] == "high" for w in warnings)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    summary = {
        "warnings": warnings,
        "overall_validation": {
            "safe": is_safe,
            "needs_manual_review": needs_review,
            "warning_count": len(warnings)
        },
        "validation_time_ms": round(elapsed_ms, 2)
    }

    logger.info(
        f"[CLINICAL_INTELLIGENCE] Validation complete ({summary['validation_time_ms']} ms). "
        f"Warnings: {len(warnings)}, Safe: {is_safe}, Review Required: {needs_review}"
    )

    if is_debug:
        try:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "clinical_validation.json"), "w", encoding="utf-8") as f_json:
                json.dump(summary, f_json, indent=2)
        except Exception as dbg_err:
            logger.warning(f"[CLINICAL_INTELLIGENCE] Debug save error: {dbg_err}")

    return summary
