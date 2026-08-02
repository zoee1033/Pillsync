import time
from typing import List
from app.schemas.ocr_schema import ExtractedMedicine, OCRExtractResponse, FieldConfidence
from app.services.ocr.preprocessor import process_image_adaptive
from app.services.ocr.ocr_engine import run_ocr_ensemble_mode
from app.services.ocr.medical_parser import parse_ocr_text_to_medicines
from app.services.ocr.ai_ocr_engine import run_openai_vision_ocr, resolve_openai_hybrid_conflict


def extract_prescription_data(image_bytes: bytes, filename: str = "") -> OCRExtractResponse:
    """
    Unified Prescription OCR Service with OpenAI Vision Cloud Fallback:
    Stage 1: Adaptive OpenCV Preprocessing
    Stage 2: Tesseract Multi-PSM Ensemble Pass
    Stage 3: OpenAI Vision Cloud Fallback Trigger & Hybrid Conflict Resolution
             (Invoked ONLY IF overall_conf < 85%, med_conf < 85%, dose_conf < 80%, or unknown drug)
    """
    if not image_bytes:
        return OCRExtractResponse(
            success=False,
            message="No image content provided",
            medicines=[]
        )

    try:
        # Stage 1: Adaptive OpenCV Preprocessing
        pil_variants, quality_analysis = process_image_adaptive(image_bytes)

        # Stage 2: Tesseract Ensemble Mode
        extracted_text, best_variant, ocr_conf, ensemble_logs = run_ocr_ensemble_mode(pil_variants)

        # Medical Parsing
        medicines = parse_ocr_text_to_medicines(extracted_text, filename=filename)

        # Stage 3: OpenAI Vision Hybrid Decision Logic
        trigger_openai_fallback = False
        if ocr_conf < 85.0 or not medicines:
            trigger_openai_fallback = True
        elif medicines:
            for m in medicines:
                if m.confidence < 0.85 or m.needs_review:
                    trigger_openai_fallback = True
                    break
                if m.field_confidence and (m.field_confidence.name_confidence < 85 or m.field_confidence.dosage_confidence < 80):
                    trigger_openai_fallback = True
                    break

        if trigger_openai_fallback:
            print(f"[HYBRID_DECISION] Fallback Criteria Met (Tesseract Conf: {ocr_conf:.1f}%). Triggering OpenAI Vision...", flush=True)
            openai_res = run_openai_vision_ocr(image_bytes)

            if openai_res.get("success") and (openai_res.get("raw_text") or openai_res.get("structured_data")):
                ai_text = openai_res.get("raw_text", "")
                ai_meds = parse_ocr_text_to_medicines(ai_text, filename=filename)

                if ai_meds:
                    for i in range(min(len(medicines), len(ai_meds))):
                        t_med = medicines[i]
                        o_med = ai_meds[i]

                        resolved_name, resolved_conf, conflict_review, details = resolve_openai_hybrid_conflict(
                            t_med.medicine_name,
                            t_med.confidence * 100.0,
                            o_med.medicine_name,
                            o_med.confidence * 100.0
                        )

                        # Structured Audit Logging
                        print(f"--- OPENAI HYBRID AUDIT LOG ---", flush=True)
                        print(f"  - Tesseract Conf:  {details['tesseract_confidence']:.1f}% | KB Score: {details['tesseract_kb_score']:.1f}%", flush=True)
                        print(f"  - OpenAI Conf:     {details['openai_confidence']:.1f}% | KB Score: {details['openai_kb_score']:.1f}%", flush=True)
                        print(f"  - Selected Engine: {details['selected_engine']}", flush=True)
                        print(f"  - Inference Time:  {openai_res.get('inference_time_ms', 0)} ms", flush=True)
                        print(f"  - Resolution:      {details['resolution_reason']}", flush=True)

                        medicines[i].medicine_name = resolved_name
                        if conflict_review:
                            medicines[i].needs_review = True

        if not medicines:
            return OCRExtractResponse(
                success=False,
                message="We couldn't recognize the prescription. Please edit manually.",
                medicines=[
                    ExtractedMedicine(
                        medicine_name="Amoxicillin",
                        dosage="500mg",
                        quantity=30,
                        frequency="Daily",
                        duration="7 days",
                        confidence=0.70,
                        field_confidence=FieldConfidence(name_confidence=75, dosage_confidence=70, frequency_confidence=65, duration_confidence=70),
                        needs_review=True
                    )
                ],
                raw_text=extracted_text or "Unrecognized image format"
            )

        return OCRExtractResponse(
            success=True,
            message=f"Prescription extracted successfully using Hybrid OCR ({best_variant})!",
            medicines=medicines,
            raw_text=extracted_text
        )

    except Exception as e:
        print(f"[OCR_SERVICE] Execution error: {e}", flush=True)
        return OCRExtractResponse(
            success=False,
            message=f"OCR Processing Error: {str(e)}",
            medicines=[]
        )
