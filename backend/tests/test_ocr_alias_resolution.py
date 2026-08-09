import unittest
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz, load_medicine_database


class TestOCRAliasResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_medicine_database()

    def test_rule_13_required_examples(self):
        """Rule 13: Verify required OCR alias examples resolve to correct generic medicines."""
        test_cases = [
            ("CALPOL", "Paracetamol"),
            ("CALP0L", "Paracetamol"),
            ("CALPOI", "Paracetamol"),
            ("Cal Pol", "Paracetamol"),
            ("Calpol 250", "Paracetamol"),
            ("Calpol DS", "Paracetamol"),
            ("Meftal P", "Mefenamic Acid"),
            ("Meftal-P", "Mefenamic Acid"),
            ("LEV0LIN", "Levosalbutamol"),
            ("LEVOLIN", "Levosalbutamol"),
            ("Tab Calpol", "Paracetamol"),
            ("Syp Calpol", "Paracetamol"),
        ]

        for candidate, expected_generic in test_cases:
            with self.subTest(candidate=candidate):
                res = match_medicine_rapidfuzz(candidate)
                self.assertTrue(res.get("is_known"), f"Candidate '{candidate}' failed to match in database.")
                self.assertEqual(
                    res.get("generic_name"),
                    expected_generic,
                    f"Candidate '{candidate}' resolved to '{res.get('generic_name')}', expected '{expected_generic}'."
                )


if __name__ == "__main__":
    unittest.main()
