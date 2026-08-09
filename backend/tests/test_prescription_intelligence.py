import unittest
import time
from app.services.ocr.prescription_intelligence import process_prescription_intelligence


class TestPrescriptionIntelligence(unittest.TestCase):

    def test_single_medicine(self):
        """Test intelligence grouping for a single medicine prescription."""
        text = "Tab Calpol 650 mg 1-0-1 5 Days After Food"
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(meta["group_count"], 1)
        self.assertFalse(meta["fallback_used"])
        self.assertLess(meta["execution_time_ms"], 20.0)

    def test_multiple_medicines(self):
        """Test grouping multiple distinct medicines."""
        text = """
        Tab Calpol 650 mg 1-0-1 5 Days
        Cap Azithromycin 500 mg OD 3 Days
        Syp Levolin 5 ml TDS 5 Days
        """
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(meta["group_count"], 3)
        self.assertFalse(meta["fallback_used"])

    def test_bullet_points(self):
        """Test handling bulleted prescription items (1., 2., 3., •)."""
        text = """
        1. Tab Calpol 650 mg 1-0-1
        2. Cap Azithromycin 500 mg OD
        3. Syp Levolin 5 ml TDS
        """
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 3)
        self.assertEqual(meta["group_count"], 3)

    def test_continuation_lines(self):
        """Test continuation lines (dosage, frequency, instructions on next line)."""
        text = """
        Tab Calpol
        650 mg
        1-0-1
        5 Days
        After Food
        
        Cap Azithromycin
        500 mg
        OD
        3 Days
        """
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 2)
        self.assertIn("650 mg", blocks[0]["medicine_lines"])
        self.assertIn("After Food", blocks[0]["medicine_lines"])

    def test_blank_lines(self):
        """Test robust handling of blank/empty lines."""
        text = "\n\n  \n Tab Calpol 500mg \n\n Syp Levolin 5ml \n\n"
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 2)

    def test_mixed_handwriting_shorthand(self):
        """Test mixed case, handwriting OCR artifacts, and doctor shorthand."""
        text = """
        syp CALPOL (250/5) 4 mL Q6H x 3 d
        syp DELCON 3 mL TDS x 5 d
        """
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 2)
        self.assertIn("Q6H", blocks[0]["medicine_lines"][0])

    def test_missing_dosage(self):
        """Test missing dosage does not fabricate any value."""
        text = "Tab Calpol 1-0-1 5 Days"
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["dosage"], "")

    def test_missing_duration(self):
        """Test missing duration does not fabricate any value."""
        text = "Tab Calpol 650 mg 1-0-1"
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["duration"], "")

    def test_missing_frequency(self):
        """Test missing frequency does not fabricate any value."""
        text = "Tab Calpol 650 mg for 5 Days"
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["frequency"], "")

    def test_header_and_footer_noise(self):
        """Test non-prescription header and footer noise filtering."""
        text = """
        Dr. Nithin Narayanan MBBS MD
        Reg No: 52547 Ph: 8086993168
        Date: 20-09-2022 Name: ASHVIKA
        Clinical Description: URTI
        Advice:
        Tab Calpol 650 mg 1-0-1 5 Days
        Syp Levolin 5 ml TDS 5 Days
        Doctor Signature / Stamp
        """
        blocks, meta = process_prescription_intelligence(text)

        self.assertEqual(len(blocks), 2)

    def test_performance_under_20ms(self):
        """Test execution latency is strictly below 20 ms."""
        text = """
        1. Tab Calpol 650 mg 1-0-1 5 Days After Food
        2. Cap Azithromycin 500 mg OD 3 Days
        3. Syp Levolin 5 ml TDS 5 Days
        4. Tab Pantop 40 mg 1-0-0 ac
        5. Tab Cetirizine 10 mg 0-0-1
        """
        t0 = time.perf_counter()
        blocks, meta = process_prescription_intelligence(text)
        t_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(t_ms, 20.0, f"Execution took {t_ms:.2f} ms, target < 20 ms")
        self.assertEqual(len(blocks), 5)


if __name__ == "__main__":
    unittest.main()
