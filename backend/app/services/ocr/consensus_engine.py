import os
import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from rapidfuzz import fuzz

from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence

logger = logging.getLogger("CONSENSUS_ENGINE")

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))


def run_multi_provider_consensus(
    provider_results: Dict[str, Tuple[List[ExtractedMedicine], float, float]]
) -> Tuple[List[ExtractedMedicine], float, Dict[str, Any]]:
    """
    Consensus AI Engine:
    Evaluates predictions across multiple vision providers simultaneously (e.g. Gemma, Gemini, GPT).
    Implements majority voting, weighted confidence aggregation, agreement percentage, and consensus scoring.
    """
    start_time = time.perf_counter()
    logger.info(f"[CONSENSUS] Evaluating consensus across {len(provider_results)} provider(s)")

    if not provider_results:
        return [], 0.0, {}

    if len(provider_results) == 1:
        prov_id = list(provider_results.keys())[0]
        meds, conf, latency = provider_results[prov_id]
        return meds or [], conf, {
            "consensus_score": 100.0,
            "agreement_percentage": 100.0,
            "winning_provider": prov_id,
            "provider_count": 1
        }

    # Aggregate candidate medicines across all providers
    all_candidates: List[Tuple[str, ExtractedMedicine, float]] = []
    for prov_id, (meds, conf, latency) in provider_results.items():
        if meds:
            for m in meds:
                all_candidates.append((prov_id, m, conf))

    if not all_candidates:
        return [], 0.0, {"consensus_score": 0.0, "provider_count": len(provider_results)}

    # Cluster medicines by fuzzy name match
    clusters: List[List[Tuple[str, ExtractedMedicine, float]]] = []
    for prov_id, m, conf in all_candidates:
        matched_cluster = None
        for clus in clusters:
            rep_med = clus[0][1]
            if fuzz.WRatio(m.medicine_name.lower(), rep_med.medicine_name.lower()) >= 80:
                matched_cluster = clus
                break
        if matched_cluster:
            matched_cluster.append((prov_id, m, conf))
        else:
            clusters.append([(prov_id, m, conf)])

    consensus_meds: List[ExtractedMedicine] = []
    voting_details: List[Dict[str, Any]] = []

    for clus in clusters:
        votes_count = len(clus)
        provider_ids = [c[0] for c in clus]
        rep_med = clus[0][1]

        # Majority vote for dosage and frequency
        dosages = [c[1].dosage for c in clus if c[1].dosage]
        frequencies = [c[1].frequency for c in clus if c[1].frequency]
        durations = [c[1].duration for c in clus if c[1].duration]
        quantities = [c[1].quantity for c in clus if c[1].quantity is not None]

        best_dosage = max(set(dosages), key=dosages.count) if dosages else rep_med.dosage
        best_freq = max(set(frequencies), key=frequencies.count) if frequencies else rep_med.frequency
        best_dur = max(set(durations), key=durations.count) if durations else rep_med.duration
        best_qty = max(set(quantities), key=quantities.count) if quantities else rep_med.quantity

        weighted_conf = sum(c[2] for c in clus) / len(clus)
        agreement_pct = (votes_count / len(provider_results)) * 100.0

        consensus_med = ExtractedMedicine(
            medicine_name=rep_med.medicine_name,
            dosage=best_dosage,
            quantity=best_qty,
            frequency=best_freq,
            duration=best_dur,
            confidence=round(weighted_conf, 2),
            field_confidence=FieldConfidence(
                name_confidence=int(agreement_pct),
                dosage_confidence=90 if best_dosage else 50,
                frequency_confidence=90 if best_freq else 50,
                duration_confidence=90 if best_dur else 50
            ),
            needs_review=agreement_pct < 60.0
        )
        consensus_meds.append(consensus_med)
        voting_details.append({
            "medicine_name": rep_med.medicine_name,
            "votes_count": votes_count,
            "participating_providers": provider_ids,
            "agreement_percentage": round(agreement_pct, 1)
        })

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    overall_consensus_score = round(
        sum(v["agreement_percentage"] for v in voting_details) / len(voting_details), 1
    ) if voting_details else 0.0

    consensus_report = {
        "consensus_score": overall_consensus_score,
        "participating_providers": list(provider_results.keys()),
        "total_providers": len(provider_results),
        "voting_details": voting_details,
        "execution_time_ms": elapsed_ms
    }

    if DEBUG_OCR or os.path.exists(DEBUG_DIR):
        try:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            with open(os.path.join(DEBUG_DIR, "consensus_report.json"), "w", encoding="utf-8") as f_cns:
                json.dump(consensus_report, f_cns, indent=2)
        except Exception as dbg_err:
            logger.warning(f"[CONSENSUS] Debug report error: {dbg_err}")

    logger.info(f"[CONSENSUS] Final consensus score: {overall_consensus_score}% ({len(consensus_meds)} medicines, {elapsed_ms}ms)")
    return consensus_meds, overall_consensus_score, consensus_report
