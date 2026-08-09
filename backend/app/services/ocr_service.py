import os
import time
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
from app.schemas.ocr_schema import ExtractedMedicine, OCRExtractResponse, FieldConfidence
from app.services.ocr.preprocessor import process_image_adaptive
from app.services.ocr.ocr_engine import run_ocr_ensemble_mode
from app.services.ocr.medical_parser import parse_ocr_text_to_medicines
from app.services.ocr.ai_ocr_engine import (
    run_gemini_vision_verification,
    convert_gemini_response_to_medicines,
    run_openai_vision_ocr,
    resolve_openai_hybrid_conflict,
    OCR_CONFIDENCE_THRESHOLD,
    FIELD_CONFIDENCE_THRESHOLD,
    MEDICINE_CONFIDENCE_THRESHOLD
)

from app.services.ocr.gemma_vision import GemmaVisionService, USE_GEMMA

logger = logging.getLogger(__name__)


def evaluate_gemini_trigger(
    ocr_conf: float,
    medicines: List[ExtractedMedicine]
) -> Tuple[bool, str]:
    """
    Task 4: Evaluates multiple conditions to decide whether Gemini / Gemma Vision Verification is required.
    Triggers Vision Fallback if ANY of the following conditions are met:
    1. OCR confidence below threshold (ocr_conf < OCR_CONFIDENCE_THRESHOLD)
    2. No medicines detected (not medicines)
    3. Parser failed (any medicine name is missing or unknown)
    4. RapidFuzz validation failed (field confidence < FIELD_CONFIDENCE_THRESHOLD)
    5. needs_review is already True
    """
    if ocr_conf < OCR_CONFIDENCE_THRESHOLD:
        return True, f"OCR confidence ({ocr_conf:.1f}%) below threshold ({OCR_CONFIDENCE_THRESHOLD}%)"

    if not medicines:
        return True, "No medicines detected by Tesseract parser"

    for m in medicines:
        if not m.medicine_name or m.medicine_name.lower() in ["unknown", "unrecognized"]:
            return True, f"Parser failed for medicine candidate '{m.medicine_name}'"

        if m.field_confidence and (
            m.field_confidence.name_confidence < FIELD_CONFIDENCE_THRESHOLD or
            m.field_confidence.dosage_confidence < FIELD_CONFIDENCE_THRESHOLD
        ):
            return True, f"RapidFuzz validation score low for '{m.medicine_name}'"

        if m.confidence < MEDICINE_CONFIDENCE_THRESHOLD:
            return True, f"Overall confidence ({m.confidence}) below threshold ({MEDICINE_CONFIDENCE_THRESHOLD})"

        if m.needs_review:
            return True, f"Medicine '{m.medicine_name}' flagged for review"

    return False, "All confidence and validation criteria satisfied"


def extract_prescription_data(image_bytes: bytes, filename: str = "") -> OCRExtractResponse:
    """
    Target Pipeline:
    Prescription Upload → Image Analyzer → OpenCV Preprocessing → Tesseract OCR →
    Knowledge Base Validation → Medical Parser → Prescription Intelligence →
    (If required) Gemma-4 Vision / Gemini Vision Verification → Clinical Intelligence → OCRExtractResponse
    """
    import uuid
    pipeline_start_time = time.time()
    trace_id = f"tr_ocr_{uuid.uuid4().hex[:10]}"
    if not image_bytes:
        return OCRExtractResponse(
            success=False,
            message="No image content provided",
            medicines=[]
        )

    try:
        # Stage 1: Adaptive OpenCV Preprocessing
        t_prep_start = time.time()
        pil_variants, quality_analysis = process_image_adaptive(image_bytes)
        prep_time_ms = round((time.time() - t_prep_start) * 1000, 2)

        # Stage 2: Crop-by-Crop Tesseract OCR Ensemble
        logger.info(f"[TESSERACT] [TraceID={trace_id}] Started OCR ensemble processing")
        t_ocr_start = time.time()
        extracted_text, best_variant, ocr_conf, ensemble_logs = run_ocr_ensemble_mode(pil_variants)
        ocr_time_ms = round((time.time() - t_ocr_start) * 1000, 2)
        best_psm = ensemble_logs[0].get("psm", "--psm 6 --oem 3") if ensemble_logs else "--psm 6 --oem 3"
        logger.info(f"[TESSERACT] [TraceID={trace_id}] Completed ({ocr_time_ms}ms). Variant='{best_variant}', PSM='{best_psm}', OCR Conf={ocr_conf:.1f}%")

        # Stage 3: Medical Parsing & Knowledge Base Lookup on Tesseract Output
        logger.info(f"[PARSER] [TraceID={trace_id}] Parsing OCR text to structured medicines")
        t_parse_start = time.time()
        tesseract_meds = parse_ocr_text_to_medicines(extracted_text, filename=filename)
        parse_time_ms = round((time.time() - t_parse_start) * 1000, 2)
        logger.info(f"[PARSER] [TraceID={trace_id}] Completed ({parse_time_ms}ms). Extracted {len(tesseract_meds)} medicine candidate(s)")

        ai_provider = os.getenv("AI_PROVIDER", "auto")
        ai_model = os.getenv("GEMMA_MODEL", os.getenv("AI_MODEL", "google/gemma-3-27b-it"))
        provider_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        logger.info(f"[MODEL_CONFIG] AI_PROVIDER='{ai_provider}' | AI_MODEL='{ai_model}' | Provider Endpoint='{provider_endpoint}' | Actual Model Used='google/gemma-3-27b-it'")

        # Stage 4: Vision AI Verification & Provider Abstraction (Controlled by FUSION_MODE)
        from app.config import settings
        from app.services.ocr.providers.vision_provider_factory import VisionProviderFactory
        fusion_mode = getattr(settings, "FUSION_MODE", "always").lower().strip()
        
        should_run_vision = False
        if fusion_mode == "always":
            should_run_vision = True
        elif fusion_mode == "smart":
            should_run_vision = (ocr_conf < 80.0) or not tesseract_meds or any(m.needs_review for m in tesseract_meds)
        elif fusion_mode == "tesseract_only":
            should_run_vision = False

        gemma_meds: List[ExtractedMedicine] = []
        gemma_conf: float = 0.0
        gemma_latency_ms: float = 0.0
        active_provider_id = "none"

        if should_run_vision and USE_GEMMA:
            # Phase 1, 2 & 12: Dynamic Provider Factory & Failure Recovery Chain
            fallback_chain = ["gemma", "gemini", "gpt"]
            for prov_name in fallback_chain:
                try:
                    logger.info(f"[VISION_PROVIDER] [TraceID={trace_id}] Attempting Provider '{prov_name}' (Mode='{fusion_mode}')")
                    provider = VisionProviderFactory.get_provider(prov_name)
                    if provider.initialize():
                        v_meds, v_conf, v_latency = provider.extract_prescription(image_bytes)
                        if v_meds:
                            gemma_meds = v_meds
                            gemma_conf = v_conf
                            gemma_latency_ms = v_latency
                            active_provider_id = provider.provider_id
                            logger.info(f"[VISION_PROVIDER] [TraceID={trace_id}] Provider '{prov_name}' successful ({v_latency}ms). Extracted {len(v_meds)} candidate medicine(s)")
                            break
                except Exception as prov_err:
                    logger.warning(f"[VISION_PROVIDER] [TraceID={trace_id}] Provider '{prov_name}' failed: {prov_err}. Trying fallback...")

        else:
            logger.info(f"[VISION_PROVIDER] [TraceID={trace_id}] Skipped (FUSION_MODE='{fusion_mode}', USE_GEMMA={USE_GEMMA})")

        # Trace Log Raw Tesseract and Raw Gemma Candidates
        logger.info(f"[TRACE_OCR_FLOW] TESSERACT_CANDIDATES ({len(tesseract_meds)} items): " + json.dumps([{"name": m.medicine_name, "dosage": m.dosage, "freq": m.frequency, "dur": m.duration, "conf": m.confidence} for m in tesseract_meds]))
        logger.info(f"[TRACE_OCR_FLOW] GEMMA_CANDIDATES ({len(gemma_meds)} items): " + json.dumps([{"name": m.medicine_name, "dosage": m.dosage, "freq": m.frequency, "dur": m.duration, "conf": m.confidence} for m in gemma_meds]))

        # Stage 5: Intelligent Field-Level Result Fusion Engine
        from app.services.ocr.fusion_engine import fuse_field_level_medicines
        fused_medicines, fusion_conf, fusion_report = fuse_field_level_medicines(
            tesseract_meds=tesseract_meds,
            gemma_meds=gemma_meds,
            tesseract_conf=ocr_conf,
            gemma_conf=gemma_conf,
            trace_id=trace_id
        )
        medicines = fused_medicines
        logger.info(f"[TRACE_OCR_FLOW] FUSION_MEDICINES ({len(medicines)} items): " + json.dumps([{"name": m.medicine_name, "dosage": m.dosage, "freq": m.frequency, "dur": m.duration, "conf": m.confidence, "review": m.needs_review} for m in medicines]))

        # Stage 6: Conditional Fallback Evaluation for Legacy Gemini Verification
        trigger_vision = False
        trigger_reason = "Vision AI already provided results"
        if not gemma_meds:
            trigger_vision, trigger_reason = evaluate_gemini_trigger(fusion_conf * 100.0, medicines)

        # Stage 5: Gemini Vision Verification Layer
        gemini_time_ms = 0.0
        if trigger_vision:
            t_gemini_start = time.time()
            enhanced_bytes = None
            if pil_variants:
                best_img = None
                for v_name, img in pil_variants:
                    if v_name == best_variant:
                        best_img = img
                        break
                if not best_img and pil_variants:
                    best_img = pil_variants[0][1]

                if best_img:
                    import io
                    buf = io.BytesIO()
                    best_img.save(buf, format="PNG")
                    enhanced_bytes = buf.getvalue()

            detected_meds_payload = [
                {
                    "name": m.medicine_name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "duration": m.duration,
                    "confidence": m.confidence
                }
                for m in medicines
            ]

            logger.info(f"[OCR_SERVICE] Triggering Gemini Vision Verification. Reason: {trigger_reason}")
            gemini_res = run_gemini_vision_verification(
                image_bytes=image_bytes,
                tesseract_text=extracted_text,
                enhanced_image_bytes=enhanced_bytes,
                ocr_confidence=ocr_conf,
                detected_medicines=detected_meds_payload
            )
            gemini_time_ms = round((time.time() - t_gemini_start) * 1000, 2)

            if gemini_res.get("success") and gemini_res.get("data"):
                verified_meds = convert_gemini_response_to_medicines(gemini_res["data"])
                if verified_meds:
                    medicines = verified_meds
                    final_conf = round(sum(m.confidence for m in medicines) / len(medicines), 2)
                    logger.info(f"[OCR_SERVICE] Gemini Vision Verification successful! Extracted {len(medicines)} medicine(s). Final Confidence={final_conf}")
                else:
                    logger.info("[OCR_SERVICE] Gemini Vision returned structured data but no valid medicines extracted.")
            else:
                logger.warning(f"[OCR_SERVICE] Gemini Vision Verification skipped or failed ({gemini_res.get('error')}). Retaining Tesseract OCR result with needs_review=True.")
                if medicines:
                    for m in medicines:
                        m.needs_review = True

        total_pipeline_time_ms = round((time.time() - pipeline_start_time) * 1000, 2)
        review_count = sum(1 for m in medicines if m.needs_review)
        final_conf_avg = round(sum(m.confidence for m in medicines) / len(medicines), 2) if medicines else 0.0

        # Operational Stage Timing & Performance Metrics Logging
        perf_metrics = {
            "trace_id": trace_id,
            "filename": filename,
            "timing_ms": {
                "preprocessing": prep_time_ms,
                "tesseract_ocr": ocr_time_ms,
                "medical_parsing": parse_time_ms,
                "gemma_vision": gemma_latency_ms,
                "fusion_engine": fusion_report.get("execution_time_ms", 0.0),
                "gemini_verification": gemini_time_ms,
                "total_pipeline": total_pipeline_time_ms
            },
            "medicines_extracted": len(medicines),
            "average_confidence": final_conf_avg,
            "needs_review_count": review_count
        }
        
        DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
        DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "debug"))
        if DEBUG_OCR or os.path.exists(DEBUG_DIR):
            try:
                os.makedirs(DEBUG_DIR, exist_ok=True)
                with open(os.path.join(DEBUG_DIR, "performance_metrics.json"), "w", encoding="utf-8") as f_perf:
                    json.dump(perf_metrics, f_perf, indent=2)
            except Exception as perf_err:
                logger.warning(f"[OCR_SERVICE] Performance metrics save error: {perf_err}")

        logger.info(f"[STAGE_TIMING] [TraceID={trace_id}] Preprocessing: {prep_time_ms}ms | Tesseract: {ocr_time_ms}ms | Parsing: {parse_time_ms}ms | Gemma: {gemma_latency_ms}ms | Total Pipeline: {total_pipeline_time_ms}ms")
        logger.info(f"[OCR_STATISTICS] Preprocessing Variant: '{best_variant}' | PSM: '{best_psm}' | OCR Conf: {ocr_conf:.1f}% | Medicine Count: {len(medicines)} | Avg Confidence: {final_conf_avg:.2f} | Needs Review Count: {review_count}")

        from app.services.ocr.fusion_engine import final_medicine_validation
        medicines = final_medicine_validation(medicines)
        final_conf_avg = round(sum(m.confidence for m in medicines) / len(medicines), 2) if medicines else 0.0
        review_count = sum(1 for m in medicines if m.needs_review)

        if not medicines:
            logger.info("[OCR_PIPELINE] No valid medicines recognized. Returning empty result with needs_review=True.")
            return OCRExtractResponse(
                success=False,
                message="Unable to recognize the prescription. Please review manually.",
                medicines=[],
                raw_text=extracted_text or ""
            )

        resp = OCRExtractResponse(
            success=True,
            message=f"Prescription extracted successfully using Hybrid Pipeline ({best_variant})!",
            medicines=medicines,
            raw_text=extracted_text
        )
        logger.info(f"[TRACE_OCR_FLOW] RESPONSE_JSON: " + resp.model_dump_json())
        return resp

    except Exception as e:
        logger.error(f"[OCR_SERVICE] Pipeline execution error: {e}", exc_info=True)
        return OCRExtractResponse(
            success=False,
            message=f"OCR Processing Error: {str(e)}",
            medicines=[]
        )

