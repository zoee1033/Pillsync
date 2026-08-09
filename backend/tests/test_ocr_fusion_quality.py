import unittest
from app.schemas.ocr_schema import ExtractedMedicine
from app.services.ocr.fusion_engine import (
    classify_candidate,
    is_valid_medicine_candidate,
    fuse_field_level_medicines,
)
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz


class TestOCRFusionQuality(unittest.TestCase):

    def test_1_dd_form_1289_rejected(self):
        """TEST 1: 'DD Form 1289' form header must be rejected."""
        med = ExtractedMedicine(medicine_name="DD Form 1289")
        is_valid, classification, reason = is_valid_medicine_candidate(med, [])
        self.assertFalse(is_valid)
        self.assertIn(classification, ("ADMINISTRATIVE", "HEADER_NOISE"))

    def test_2_full_name_address_phone_rejected(self):
        """TEST 2: Patient demographic/form line must be rejected."""
        med = ExtractedMedicine(
            medicine_name="Ei in os a for (full name, address, & phone number) (if under 12, give age) John K Doe"
        )
        is_valid, classification, reason = is_valid_medicine_candidate(med, [])
        self.assertFalse(is_valid)
        self.assertIn(classification, ("ADMINISTRATIVE", "PARAGRAPH_NOISE"))

    def test_3_lot_no_signature_rejected(self):
        """TEST 3: Manufacturer/Lot/Signature OCR noise must be rejected."""
        med = ExtractedMedicine(
            medicine_name="MFGR ... LOT NO 394/06 ... SIGNATURE RANK AND DEGREE"
        )
        is_valid, classification, reason = is_valid_medicine_candidate(med, [])
        self.assertFalse(is_valid)
        self.assertIn(classification, ("ADMINISTRATIVE", "PARAGRAPH_NOISE"))

    def test_4_garbled_tesseract_and_gemma_belladonna_clustered(self):
        """TEST 4: Garbled Tesseract line + clean Gemma 'Tri Belladonna' -> 1 medicine: Tri Belladonna."""
        tess_meds = [
            ExtractedMedicine(
                medicine_name="Tn bllideyrre 15 ... MFGR ... LOT NO ... SIGNATURE RANK AND DEGREE",
                dosage="15 ml"
            )
        ]
        gemma_meds = [
            ExtractedMedicine(
                medicine_name="Tri Belladonna",
                dosage="15 ml",
                confidence=0.95
            )
        ]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("Tri Belladonna", fused[0].medicine_name)
        self.assertEqual(fused[0].dosage, "15 ml")

    def test_5_amphogel_120ml_fused(self):
        """TEST 5: 'Amphogel 120 ml' fused into 1 clean medicine card."""
        tess_meds = [ExtractedMedicine(medicine_name="Amphogel", dosage="120 ml")]
        gemma_meds = [ExtractedMedicine(medicine_name="Amphogel", dosage="120 ml", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("Amphogel", fused[0].medicine_name)
        self.assertEqual(fused[0].dosage, "120 ml")

    def test_6_m_and_fi_solution_not_mapped_to_glimepiride_metformin(self):
        """TEST 6: 'M & FI Solution' compounding phrase must NOT map to Glimepiride + Metformin or Lactulose."""
        kb_match = match_medicine_rapidfuzz("M & FI Solution")
        self.assertFalse(kb_match.get("is_known"))

        med = ExtractedMedicine(medicine_name="M & FI Solution")
        is_valid, classification, reason = is_valid_medicine_candidate(med, [])
        self.assertFalse(is_valid)

    def test_7_calpol_brand_generic_preserved(self):
        """TEST 7: CALPOL -> CALPOL (Paracetamol)."""
        tess_meds = [ExtractedMedicine(medicine_name="CALPOL", dosage="50/5")]
        gemma_meds = [ExtractedMedicine(medicine_name="CALPOL", dosage="50/5", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("CALPOL", fused[0].medicine_name)
        self.assertIn("Paracetamol", fused[0].medicine_name)

    def test_8_delcon_brand_generic_preserved(self):
        """TEST 8: DELCON -> DELCON (Phenylephrine + Chlorpheniramine)."""
        tess_meds = [ExtractedMedicine(medicine_name="DELCON", dosage="3 ml")]
        gemma_meds = [ExtractedMedicine(medicine_name="DELCON", dosage="3 ml", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("DELCON", fused[0].medicine_name)

    def test_9_levolin_brand_generic_preserved(self):
        """TEST 9: LEVOLIN -> LEVOLIN (Levosalbutamol)."""
        tess_meds = [ExtractedMedicine(medicine_name="LEVOLIN", dosage="3 ml")]
        gemma_meds = [ExtractedMedicine(medicine_name="LEVOLIN", dosage="3 ml", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("LEVOLIN", fused[0].medicine_name)

    def test_10_meftal_p_brand_generic_preserved(self):
        """TEST 10: MEFTAL-P -> MEFTAL-P (Mefenamic Acid)."""
        tess_meds = [ExtractedMedicine(medicine_name="MEFTAL-P", dosage="100/5")]
        gemma_meds = [ExtractedMedicine(medicine_name="MEFTAL-P", dosage="100/5", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("MEFTAL-P", fused[0].medicine_name)

    def test_unknown_medicine_preserved_for_review(self):
        """Rule 5: Unknown medicine candidate 'CustomMedX 250mg 1-0-1' preserved with needs_review=True."""
        tess_meds = [ExtractedMedicine(medicine_name="CustomMedX", dosage="250mg", frequency="Once daily")]
        gemma_meds = [ExtractedMedicine(medicine_name="CustomMedX", dosage="250mg", frequency="Once daily", confidence=0.90)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 80.0, 90.0)
        self.assertEqual(len(fused), 1)
        self.assertIn("CustomMedX", fused[0].medicine_name)
        self.assertEqual(fused[0].dosage, "250mg")
        self.assertTrue(fused[0].needs_review)

    def test_identity_confidence_high_with_missing_optional_fields(self):
        """Confidence Scoring Fix: Missing duration/frequency must not reduce medicine identity confidence."""
        tess_meds = [ExtractedMedicine(medicine_name="Tri Belladonna", dosage="15 ml")]
        gemma_meds = [ExtractedMedicine(medicine_name="Tri Belladonna", dosage="15 ml", confidence=0.95)]
        fused, conf, _ = fuse_field_level_medicines(tess_meds, gemma_meds, 85.0, 95.0)
        self.assertEqual(len(fused), 1)
        med = fused[0]
        self.assertGreaterEqual(med.confidence, 0.85)
        self.assertIsNone(med.field_confidence.frequency_confidence)
        self.assertIsNone(med.field_confidence.duration_confidence)

    def test_final_medicine_validation_purges_m_and_fi_solution(self):
        """Rule 7: final_medicine_validation must strip M & FI Solution and form headers."""
        from app.services.ocr.fusion_engine import final_medicine_validation
        meds = [
            ExtractedMedicine(medicine_name="CALPOL", dosage="500mg"),
            ExtractedMedicine(medicine_name="M & FI Solution"),
            ExtractedMedicine(medicine_name="DD Form 1289"),
            ExtractedMedicine(medicine_name="Solution"),
        ]
        validated = final_medicine_validation(meds)
        self.assertEqual(len(validated), 1)
        self.assertIn("CALPOL", validated[0].medicine_name)


if __name__ == "__main__":
    unittest.main()
