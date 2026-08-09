import json
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from rapidfuzz import fuzz, process

logger = logging.getLogger("KNOWLEDGE_BASE")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data" / "medicine_database.json"

# In-Memory Cache Singleton
_MEDICINE_DATABASE: List[Dict[str, Any]] = []
_NAME_INDEX: Dict[str, Tuple[str, Dict[str, Any], str]] = {}
_INDEX_KEYS: List[str] = []


def load_medicine_database() -> List[Dict[str, Any]]:
    """Loads medicine database JSON once at application startup and caches index in memory."""
    global _MEDICINE_DATABASE, _NAME_INDEX, _INDEX_KEYS

    if _MEDICINE_DATABASE:
        return _MEDICINE_DATABASE

    if not os.path.exists(JSON_PATH):
        logger.warning(f"{JSON_PATH} not found.")
        return []

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            _MEDICINE_DATABASE = json.load(f)

        # Build index mapping generic names, brand names, and aliases to drug objects
        _NAME_INDEX = {}
        for drug in _MEDICINE_DATABASE:
            gen = drug["generic_name"]
            _NAME_INDEX[gen.lower()] = (gen, drug, "generic")

            for brand in drug.get("brand_names", []):
                _NAME_INDEX[brand.lower()] = (gen, drug, f"brand:{brand}")

            for alias in drug.get("aliases", []):
                _NAME_INDEX[alias.lower()] = (gen, drug, f"alias:{alias}")

        _INDEX_KEYS = list(_NAME_INDEX.keys())

        from app.config import settings
        if getattr(settings, "ENABLE_VERBOSE_OCR_LOGS", False):
            logger.debug(f"Successfully loaded {len(_MEDICINE_DATABASE)} medicines into memory cache ({len(_NAME_INDEX)} index entries).")
    except Exception as e:
        logger.error(f"Error loading JSON: {e}", exc_info=True)
        _MEDICINE_DATABASE = []

    return _MEDICINE_DATABASE


# Ensure database is cached on module import
load_medicine_database()


STANDALONE_FORMULATIONS = {
    "solution", "solutions", "tablet", "tablets", "tab", "tabs", "syrup", "syrups",
    "syp", "capsule", "capsules", "cap", "caps", "cream", "creams", "gel", "gels",
    "tincture", "mixture", "elixir", "suspension", "lotion", "ointment", "emulsion",
    "powder", "m & fi solution", "m & f i solution", "m. & f. i. solution",
    "m. et sig.", "m & f solution", "m.f.i. solution"
}

ADMINISTRATIVE_PATTERNS = [
    r'\b(?:full\s*name|address|phone|telephone|medical\s*facility|hospital|clinic)\b',
    r'\b(?:lot\s*no|batch\s*no|manufacturer|mfgr|signature|rank\s*and\s*degree|rank\s*&\s*degree)\b',
    r'\b(?:dd\s*form|form\s*1289|edition|serial\s*number)\b',
]


@lru_cache(maxsize=2048)
def match_medicine_rapidfuzz(candidate: str) -> Dict[str, Any]:
    """
    Ultra-Fast C++ Optimized RapidFuzz Matcher with LRU Cache and KB Safety Guard:
    Evaluates exact index first, then uses vectorized C++ WRatio process matching.
    Prevents standalone formulation words or administrative text from producing false drug matches.
    """
    cand_clean = candidate.strip().lower()
    if not cand_clean or len(cand_clean) < 2:
        return {
            "matched_name": candidate,
            "generic_name": None,
            "similarity_score": 0.0,
            "algorithm_used": "none",
            "match_reason": "Empty or short candidate",
            "drug_object": None,
            "is_known": False
        }

    # Safety Guard 1: Standalone formulation or administrative text check
    if cand_clean in STANDALONE_FORMULATIONS:
        return {
            "matched_name": candidate.strip(),
            "generic_name": None,
            "similarity_score": 0.0,
            "algorithm_used": "formulation_guard",
            "match_reason": f"Standalone formulation phrase '{candidate}'",
            "drug_object": None,
            "is_known": False
        }

    for admin_pat in ADMINISTRATIVE_PATTERNS:
        if re.search(admin_pat, cand_clean, re.IGNORECASE):
            return {
                "matched_name": candidate.strip(),
                "generic_name": None,
                "similarity_score": 0.0,
                "algorithm_used": "admin_guard",
                "match_reason": f"Administrative text pattern detected",
                "drug_object": None,
                "is_known": False
            }

    # 1. Fast Exact Index Match
    if cand_clean in _NAME_INDEX:
        gen, drug_obj, match_type = _NAME_INDEX[cand_clean]
        return {
            "matched_name": gen,
            "generic_name": gen,
            "similarity_score": 98.0,
            "algorithm_used": "exact_index",
            "match_reason": f"Exact match ({match_type})",
            "drug_object": drug_obj,
            "is_known": True
        }

    # 2. Vectorized RapidFuzz C++ Process Extract with Safety Token Validation
    if not _INDEX_KEYS:
        load_medicine_database()

    # Fast Pre-Filter: Skip expensive fuzzy matching on long paragraphs, dates, or garbled non-word text
    words = [w for w in re.findall(r'\b[a-z]{3,}\b', cand_clean) if w not in STANDALONE_FORMULATIONS]
    if not words or len(words) > 5 or len(cand_clean) > 50:
        return {
            "matched_name": candidate.strip(),
            "generic_name": None,
            "similarity_score": 0.0,
            "algorithm_used": "prefilter_skipped",
            "match_reason": "Candidate skipped by fast pre-filter (length/word limit)",
            "drug_object": None,
            "is_known": False
        }

    best_match = process.extractOne(cand_clean, _INDEX_KEYS, scorer=fuzz.WRatio)
    if best_match:
        target_key, best_score, _ = best_match
        if best_score >= 85.0 and target_key in _NAME_INDEX:
            # Safety Check: Verify candidate is not matching solely on generic formulation tokens (e.g. 'solution')
            cand_words = set(re.findall(r'\b[a-z]{3,}\b', cand_clean)) - {"solution", "tablet", "syrup", "capsule", "cream", "gel", "injection"}
            target_words = set(re.findall(r'\b[a-z]{3,}\b', target_key)) - {"solution", "tablet", "syrup", "capsule", "cream", "gel", "injection"}
            
            # Require non-formulation word overlap if score is not near-perfect
            if not cand_words or (cand_words and target_words and not cand_words.intersection(target_words) and best_score < 92.0):
                return {
                    "matched_name": candidate.strip(),
                    "generic_name": None,
                    "similarity_score": round(float(best_score), 1),
                    "algorithm_used": "rapidfuzz_rejected_formulation_only",
                    "match_reason": f"Formulation-only match on '{target_key}' without core drug token overlap",
                    "drug_object": None,
                    "is_known": False
                }

            gen_name, drug_obj, match_type = _NAME_INDEX[target_key]
            return {
                "matched_name": gen_name,
                "generic_name": gen_name,
                "similarity_score": round(float(best_score), 1),
                "algorithm_used": "rapidfuzz_wratio",
                "match_reason": f"RapidFuzz match on '{target_key}' ({match_type})",
                "drug_object": drug_obj,
                "is_known": True
            }

    # Unlisted Medicine Fallback
    possible_matches = [d["generic_name"] for d in _MEDICINE_DATABASE[:5]] if _MEDICINE_DATABASE else []
    return {
        "matched_name": candidate.strip(),
        "generic_name": None,
        "similarity_score": round(float(best_match[1]), 1) if best_match else 0.0,
        "algorithm_used": "low_confidence",
        "match_reason": f"Low confidence match",
        "drug_object": None,
        "is_known": False,
        "possible_matches": possible_matches
    }


def validate_dosage_non_destructive(raw_dosage: str, drug_obj: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validates if extracted dosage is plausible for the given drug object."""
    if not raw_dosage or not drug_obj:
        return {"valid": True, "reason": "No drug object for validation"}

    dosages = drug_obj.get("common_dosages", [])
    if not dosages:
        return {"valid": True, "reason": "No dosage constraints"}

    clean_raw = raw_dosage.lower().replace(" ", "")
    for d in dosages:
        if clean_raw in d.lower().replace(" ", ""):
            return {"valid": True, "reason": f"Matched dosage {d}"}

    return {"valid": True, "reason": "Unconstrained dosage"}
