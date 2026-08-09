import unittest
import time
from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence
from app.services.ocr.clinical_intelligence import validate_prescription_clinically


class TestClinicalIntelligence(unittest.TestCase):

    def test_no_warning_prescription(self):
        """Test clean prescription with valid medicines generates zero high severity warnings."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="Twice daily", duration="5 Days", confidence=0.95),
            ExtractedMedicine(medicine_name="Levolin", dosage="3 ml", frequency="Three times daily", duration="5 Days", confidence=0.92)
        ]
        summary = validate_prescription_clinically(meds)

        self.assertTrue(summary["overall_validation"]["safe"])
        self.assertEqual(summary["overall_validation"]["warning_count"], 0)
        self.assertLess(summary["validation_time_ms"], 10.0)

    def test_duplicate_generic(self):
        """Test duplicate generic detection (Calpol & Dolo -> Paracetamol)."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days"),
            ExtractedMedicine(medicine_name="Dolo", dosage="650 mg", frequency="1-0-1", duration="3 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("duplicate_generic", warning_types)
        self.assertFalse(summary["overall_validation"]["safe"])

    def test_duplicate_therapy(self):
        """Test duplicate drug class therapy (Pantoprazole & Rabeprazole -> PPIs)."""
        meds = [
            ExtractedMedicine(medicine_name="Pantop", dosage="40 mg", frequency="1-0-0", duration="7 Days"),
            ExtractedMedicine(medicine_name="Rabeprazole", dosage="20 mg", frequency="1-0-0", duration="7 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("duplicate_therapy", warning_types)

    def test_missing_dosage(self):
        """Test missing dosage warning generation."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="", frequency="1-0-1", duration="5 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("missing_dosage", warning_types)

    def test_missing_duration(self):
        """Test missing duration warning generation."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("missing_duration", warning_types)

    def test_missing_frequency(self):
        """Test missing frequency warning generation."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="", duration="5 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("missing_frequency", warning_types)

    def test_unknown_medicine(self):
        """Test unknown medicine triggers manual review flag without editing OCR data."""
        meds = [
            ExtractedMedicine(medicine_name="Unknown", dosage="500 mg", frequency="1-0-1", duration="5 Days", needs_review=True)
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("unknown_medicine", warning_types)
        self.assertTrue(summary["overall_validation"]["needs_manual_review"])

    def test_repeated_medicine(self):
        """Test repeated medicine detection in prescription."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days"),
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("repeated_medicine", warning_types)

    def test_impossible_dosage(self):
        """Test impossible dosage detection (Paracetamol 50000 mg)."""
        meds = [
            ExtractedMedicine(medicine_name="Paracetamol", dosage="50000 mg", frequency="1-0-1", duration="5 Days")
        ]
        summary = validate_prescription_clinically(meds)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("impossible_dosage", warning_types)
        self.assertFalse(summary["overall_validation"]["safe"])

    def test_low_confidence_ocr(self):
        """Test low OCR confidence flags suspicious OCR."""
        meds = [
            ExtractedMedicine(
                medicine_name="Calpol",
                dosage="500 mg",
                frequency="1-0-1",
                duration="5 Days",
                confidence=0.60,
                field_confidence=FieldConfidence(name_confidence=55, dosage_confidence=90, frequency_confidence=90, duration_confidence=90)
            )
        ]
        summary = validate_prescription_clinically(meds, ocr_conf=65.0)

        warning_types = [w["type"] for w in summary["warnings"]]
        self.assertIn("suspicious_ocr", warning_types)

    def test_performance_under_10ms(self):
        """Test execution latency is strictly under 10 ms."""
        meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days"),
            ExtractedMedicine(medicine_name="Azithromycin", dosage="500 mg", frequency="OD", duration="3 Days"),
            ExtractedMedicine(medicine_name="Levolin", dosage="5 ml", frequency="TDS", duration="5 Days"),
            ExtractedMedicine(medicine_name="Pantop", dosage="40 mg", frequency="1-0-0", duration="7 Days"),
            ExtractedMedicine(medicine_name="Cetirizine", dosage="10 mg", frequency="0-0-1", duration="5 Days")
        ]
        t0 = time.perf_counter()
        summary = validate_prescription_clinically(meds)
        t_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(t_ms, 10.0, f"Validation took {t_ms:.2f} ms, target < 10 ms")


if __name__ == "__main__":
    unittest.main()
