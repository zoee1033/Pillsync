import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz

JSON_PATH = Path(r"C:\Users\Zoya Ahmed\Desktop\Pillsync\backend\app\data\medicine_database.json")

# In-Memory Cache Singleton
_MEDICINE_DATABASE: List[Dict[str, Any]] = []
_NAME_INDEX: Dict[str, Dict[str, Any]] = {}


def load_medicine_database() -> List[Dict[str, Any]]:
    """Loads medicine database JSON once at application startup and caches index in memory."""
    global _MEDICINE_DATABASE, _NAME_INDEX

    if _MEDICINE_DATABASE:
        return _MEDICINE_DATABASE

    if not os.path.exists(JSON_PATH):
        print(f"[KNOWLEDGE_BASE] Warning: {JSON_PATH} not found.", flush=True)
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

        print(f"[KNOWLEDGE_BASE] Successfully loaded {len(_MEDICINE_DATABASE)} medicines into memory cache ({len(_NAME_INDEX)} index entries).", flush=True)
    except Exception as e:
        print(f"[KNOWLEDGE_BASE] Error loading JSON: {e}", flush=True)
        _MEDICINE_DATABASE = []

    return _MEDICINE_DATABASE


# Ensure database is cached on module import
load_medicine_database()


def match_medicine_rapidfuzz(candidate: str) -> Dict[str, Any]:
    """
    RapidFuzz Multi-Algorithm Engine:
    Evaluates WRatio, token_set_ratio, token_sort_ratio, partial_ratio, ratio.
    Maps Brand Names -> Generic Names, corrects OCR typos, and returns match metadata.
    """
    cand_clean = candidate.strip().lower()
    if not cand_clean or len(cand_clean) < 2:
        return {
            "matched_name": candidate,
            "generic_name": "Unknown",
            "similarity_score": 0.0,
            "algorithm_used": "none",
            "match_reason": "Empty or short candidate",
            "drug_object": None,
            "is_known": False
        }

    # 1. Exact Index Match Check
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

    # 2. RapidFuzz Multi-Algorithm Evaluation
    best_target = None
    best_score = 0.0
    best_algo = "none"
    best_drug_obj = None
    best_gen_name = None
    best_match_reason = ""

    for target_key, (gen_name, drug_obj, match_type) in _NAME_INDEX.items():
        # Evaluate 5 RapidFuzz algorithms
        scores = {
            "WRatio": fuzz.WRatio(cand_clean, target_key),
            "token_set_ratio": fuzz.token_set_ratio(cand_clean, target_key),
            "token_sort_ratio": fuzz.token_sort_ratio(cand_clean, target_key),
            "partial_ratio": fuzz.partial_ratio(cand_clean, target_key),
            "ratio": fuzz.ratio(cand_clean, target_key)
        }

        # Find highest scoring algorithm for this target key
        top_algo = max(scores, key=scores.get)
        top_val = scores[top_algo]

        if top_val > best_score:
            best_score = top_val
            best_algo = top_algo
            best_target = target_key
            best_drug_obj = drug_obj
            best_gen_name = gen_name
            best_match_reason = f"RapidFuzz {top_algo} match on '{target_key}' ({match_type})"

    # Minimum threshold score
    if best_score >= 70.0 and best_drug_obj:
        return {
            "matched_name": best_gen_name,
            "generic_name": best_gen_name,
            "similarity_score": round(best_score, 1),
            "algorithm_used": best_algo,
            "match_reason": best_match_reason,
            "drug_object": best_drug_obj,
            "is_known": True
        }

    # Unknown Medicine Fallback
    possible_matches = []
    if _MEDICINE_DATABASE:
        possible_matches = [d["generic_name"] for d in _MEDICINE_DATABASE[:5]]

    return {
        "matched_name": candidate.capitalize(),
        "generic_name": "Unknown",
        "similarity_score": round(best_score, 1),
        "algorithm_used": best_algo,
        "match_reason": f"Low confidence match ({best_score:.1f}%)",
        "drug_object": None,
        "is_known": False,
        "possible_matches": possible_matches
    }


def validate_dosage_non_destructive(raw_dosage: str, drug_obj: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Non-Destructive Dosage Validation:
    Preserves raw OCR text (e.g. '50000mg' or '400mg').
    Never overwrites raw OCR output. Returns validity, needs_review flag, and suggested dosages.
    """
    raw_clean = raw_dosage.strip().lower()

    if not drug_obj:
        return {
            "ocr_value": raw_dosage,
            "valid": True if raw_dosage else False,
            "needs_review": False,
            "suggested_dosages": ["500mg"]
        }

    valid_dosages = [d.lower() for d in drug_obj.get("dosages", [])]

    # Exact dosage match
    if raw_clean in valid_dosages:
        return {
            "ocr_value": raw_dosage,
            "valid": True,
            "needs_review": False,
            "suggested_dosages": drug_obj.get("dosages", [])
        }

    # Invalid or Out-of-Bound Dosage
    return {
        "ocr_value": raw_dosage,
        "valid": False,
        "needs_review": True,
        "suggested_dosages": drug_obj.get("dosages", ["500mg"])
    }
