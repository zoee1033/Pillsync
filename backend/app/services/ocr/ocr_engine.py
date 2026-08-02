import os
import pytesseract
from typing import List, Tuple, Dict, Any
from PIL import Image

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


def score_ocr_candidate(text: str, mean_conf: float) -> Tuple[float, Dict[str, Any]]:
    """
    Scores an OCR candidate based on Tesseract confidence, medical dictionary match,
    dosage validity, frequency validity, and duration validity.
    """
    from app.services.ocr.medical_parser import parse_ocr_text_to_medicines

    parsed_meds = parse_ocr_text_to_medicines(text)
    if not parsed_meds:
        return (mean_conf * 0.1), {"meds_count": 0, "name_valid": False, "dosage_valid": False, "freq_valid": False}

    name_score = len(parsed_meds) * 150.0
    dosage_score = sum(50.0 for m in parsed_meds if m.dosage and m.field_confidence and m.field_confidence.dosage_confidence >= 80)
    freq_score = sum(50.0 for m in parsed_meds if m.frequency and m.field_confidence and m.field_confidence.frequency_confidence >= 80)
    dur_score = sum(30.0 for m in parsed_meds if m.duration and m.field_confidence and m.field_confidence.duration_confidence >= 80)
    conf_weight = mean_conf * 0.5

    total_score = name_score + dosage_score + freq_score + dur_score + conf_weight

    metrics = {
        "meds_count": len(parsed_meds),
        "name_valid": name_score > 0,
        "dosage_valid": dosage_score > 0,
        "freq_valid": freq_score > 0,
        "dur_valid": dur_score > 0,
        "meds": [m.medicine_name for m in parsed_meds]
    }

    return total_score, metrics


def run_ocr_ensemble_mode(pil_variants: List[Tuple[str, Image.Image]]) -> Tuple[str, str, float, List[Dict[str, Any]]]:
    """
    OCR Ensemble Engine:
    Runs multiple Tesseract Page Segmentation Modes (--psm 3, 4, 6, 11, 12, 13) across
    preprocessed image variants and scores candidates using OCR confidence + Medical AI validity.
    Retries fallback PSMs automatically if confidence < 80%.
    """
    ensemble_logs: List[Dict[str, Any]] = []

    primary_psms = ["--psm 6 --oem 3", "--psm 4 --oem 3", "--psm 3 --oem 3"]
    fallback_psms = ["--psm 11 --oem 3", "--psm 12 --oem 3", "--psm 13 --oem 3"]

    best_text = ""
    best_variant_name = "scaled_gray"
    best_psm_used = "--psm 6 --oem 3"
    highest_score = -1.0
    best_confidence = 0.0

    # 1. Primary Ensemble Pass
    for v_name, pil_img in pil_variants:
        for psm_cfg in primary_psms:
            try:
                text = pytesseract.image_to_string(pil_img, config=psm_cfg).strip()
                if not text or len(text) < 3:
                    continue

                data = pytesseract.image_to_data(pil_img, config=psm_cfg, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data['conf'] if int(c) > 0]
                mean_conf = sum(confs) / len(confs) if confs else 0.0

                score, metrics = score_ocr_candidate(text, mean_conf)

                log_item = {
                    "variant": v_name,
                    "psm": psm_cfg,
                    "confidence": round(mean_conf, 2),
                    "score": round(score, 2),
                    "text_preview": text[:60].replace("\n", " "),
                    "meds": metrics.get("meds", []),
                    "status": "Evaluated"
                }
                ensemble_logs.append(log_item)

                if score > highest_score:
                    highest_score = score
                    best_confidence = mean_conf
                    best_text = text
                    best_variant_name = v_name
                    best_psm_used = psm_cfg

            except Exception as e:
                print(f"[OCR_ENSEMBLE] Error processing {v_name} with {psm_cfg}: {e}", flush=True)

    # 2. Low-Confidence / Low-Score Automatic Fallback Retry
    if highest_score < 150.0 or best_confidence < 80.0:
        print(f"[OCR_ENSEMBLE] Primary pass confidence/score low ({best_confidence:.1f}% / score {highest_score:.1f}). Triggering Fallback Retry...", flush=True)
        for v_name, pil_img in pil_variants:
            for psm_cfg in fallback_psms:
                try:
                    text = pytesseract.image_to_string(pil_img, config=psm_cfg).strip()
                    if not text or len(text) < 3:
                        continue

                    data = pytesseract.image_to_data(pil_img, config=psm_cfg, output_type=pytesseract.Output.DICT)
                    confs = [int(c) for c in data['conf'] if int(c) > 0]
                    mean_conf = sum(confs) / len(confs) if confs else 0.0

                    score, metrics = score_ocr_candidate(text, mean_conf)

                    log_item = {
                        "variant": v_name,
                        "psm": psm_cfg + " (Fallback Retry)",
                        "confidence": round(mean_conf, 2),
                        "score": round(score, 2),
                        "text_preview": text[:60].replace("\n", " "),
                        "meds": metrics.get("meds", []),
                        "status": "Fallback Evaluated"
                    }
                    ensemble_logs.append(log_item)

                    if score > highest_score:
                        highest_score = score
                        best_confidence = mean_conf
                        best_text = text
                        best_variant_name = v_name
                        best_psm_used = psm_cfg
                except Exception as fb_err:
                    print(f"[OCR_ENSEMBLE] Fallback error for {v_name}: {fb_err}", flush=True)

    # Fallback default if no text parsed
    if not best_text and pil_variants:
        try:
            best_text = pytesseract.image_to_string(pil_variants[0][1], config="--psm 6 --oem 3").strip()
            best_variant_name = pil_variants[0][0]
            best_psm_used = "--psm 6 --oem 3"
        except Exception:
            best_text = ""

    print(f"[OCR_ENSEMBLE] CHOSEN RESULT: Variant='{best_variant_name}', PSM='{best_psm_used}', Confidence={best_confidence:.1f}%, Score={highest_score:.1f}", flush=True)

    return best_text, best_variant_name, round(best_confidence, 2), ensemble_logs


# Backward compatibility wrapper
def run_multi_version_ocr(pil_variants: List[Tuple[str, Image.Image]]) -> Tuple[str, str, float]:
    best_text, best_variant_name, conf, _ = run_ocr_ensemble_mode(pil_variants)
    return best_text, best_variant_name, conf
