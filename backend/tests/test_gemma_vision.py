import unittest
import json
from unittest.mock import patch, MagicMock
from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence
from app.services.ocr.gemma_vision import GemmaVisionService


class TestGemmaVisionService(unittest.TestCase):

    def setUp(self):
        self.service = GemmaVisionService(api_key="test_openrouter_key", model="google/gemma-4")

    def test_initialize_client_success(self):
        """Test API key and model presence validation."""
        self.assertTrue(self.service.initialize_client())

    def test_initialize_client_missing_key(self):
        """Test missing API key validation."""
        service_no_key = GemmaVisionService(api_key="", model="google/gemma-4")
        self.assertFalse(service_no_key.initialize_client())

    def test_initialize_client_missing_model(self):
        """Test missing GEMMA_MODEL validation skips Gemma gracefully."""
        service_no_model = GemmaVisionService(api_key="test_openrouter_key", model="")
        self.assertFalse(service_no_model.initialize_client())

    def test_parse_response_clean_json(self):
        """Test parsing valid clean JSON string."""
        raw_json = '{"medicines": [{"medicine_name": "Calpol", "dosage": "500 mg"}], "confidence": 0.95}'
        parsed = self.service.parse_response(raw_json)

        self.assertIsNotNone(parsed)
        self.assertIn("medicines", parsed)
        self.assertEqual(parsed["medicines"][0]["medicine_name"], "Calpol")

    def test_parse_response_markdown_json(self):
        """Test parsing JSON wrapped inside markdown code blocks (```json ... ```)."""
        markdown_json = '```json\n{"medicines": [{"medicine_name": "Levolin", "dosage": "5 ml"}], "confidence": 0.92}\n```'
        parsed = self.service.parse_response(markdown_json)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["medicines"][0]["medicine_name"], "Levolin")

    def test_invalid_json_handling(self):
        """Test handling invalid non-JSON output."""
        invalid_text = "Sorry, I could not extract medicines from this image."
        parsed = self.service.parse_response(invalid_text)

        self.assertIsNone(parsed)
        self.assertFalse(self.service.validate_json(parsed))

    def test_convert_dict_to_extracted_medicines(self):
        """Test dict to Pydantic ExtractedMedicine model conversion."""
        data = {
            "confidence": 0.95,
            "medicines": [
                {
                    "medicine_name": "Azithromycin",
                    "dosage": "500 mg",
                    "frequency": "OD",
                    "duration": "3 Days",
                    "quantity": 3,
                    "instructions": "After food"
                }
            ]
        }
        meds = self.service.convert_dict_to_extracted_medicines(data)

        self.assertEqual(len(meds), 1)
        self.assertEqual(meds[0].medicine_name, "Azithromycin")
        self.assertEqual(meds[0].dosage, "500 mg")
        self.assertEqual(meds[0].quantity, 3)

    def test_compare_with_tesseract_gemma_better(self):
        """Test comparison where Gemma extracts complete medicines and wins."""
        tesseract_meds = [
            ExtractedMedicine(medicine_name="Unknown", dosage="", frequency="", duration="", confidence=0.40)
        ]
        gemma_meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days", confidence=0.95),
            ExtractedMedicine(medicine_name="Levolin", dosage="5 ml", frequency="TDS", duration="5 Days", confidence=0.92)
        ]

        chosen_meds, chosen_conf, reason = self.service.compare_with_tesseract(
            tesseract_meds=tesseract_meds,
            gemma_meds=gemma_meds,
            tesseract_conf=40.0,
            gemma_conf=93.5
        )

        self.assertEqual(len(chosen_meds), 2)
        self.assertEqual(chosen_meds[0].medicine_name, "Calpol")
        self.assertIn("Gemma-4 Vision", reason)

    def test_compare_with_tesseract_tesseract_better(self):
        """Test comparison where Tesseract extracts higher quality medicines and wins."""
        tesseract_meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="500 mg", frequency="1-0-1", duration="5 Days", confidence=0.95),
            ExtractedMedicine(medicine_name="Levolin", dosage="5 ml", frequency="TDS", duration="5 Days", confidence=0.92)
        ]
        gemma_meds = [
            ExtractedMedicine(medicine_name="Calpol", dosage="", frequency="", duration="", confidence=0.50)
        ]

        chosen_meds, chosen_conf, reason = self.service.compare_with_tesseract(
            tesseract_meds=tesseract_meds,
            gemma_meds=gemma_meds,
            tesseract_conf=93.5,
            gemma_conf=50.0
        )

        self.assertEqual(len(chosen_meds), 2)
        self.assertEqual(chosen_meds[0].medicine_name, "Calpol")
        self.assertIn("Tesseract OCR", reason)

    @patch("urllib.request.urlopen")
    def test_extract_prescription_successful_api_call(self, mock_urlopen):
        """Test mock successful OpenRouter API call returning Gemma vision JSON."""
        mock_response = MagicMock()
        mock_response_body = {
            "choices": [
                {
                    "message": {
                        "content": '{"medicines": [{"medicine_name": "Pantop", "dosage": "40 mg", "frequency": "1-0-0", "duration": "7 Days"}], "confidence": 0.95}'
                    }
                }
            ]
        }
        mock_response.read.return_value = json.dumps(mock_response_body).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        meds, conf, latency = self.service.extract_prescription(b"dummy_image_bytes")

        self.assertIsNotNone(meds)
        self.assertEqual(len(meds), 1)
        self.assertEqual(meds[0].medicine_name, "Pantop")
        self.assertGreater(latency, 0.0)

    @patch("urllib.request.urlopen")
    def test_extract_prescription_retry_on_invalid_json(self, mock_urlopen):
        """Test retry logic on invalid JSON output."""
        mock_response_bad = MagicMock()
        mock_response_bad.read.return_value = json.dumps({"choices": [{"message": {"content": "Invalid text response"}}]}).encode("utf-8")

        mock_response_good = MagicMock()
        mock_response_good.read.return_value = json.dumps({"choices": [{"message": {"content": '{"medicines": [{"medicine_name": "Dolo", "dosage": "650 mg"}], "confidence": 0.90}'}}]}).encode("utf-8")

        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=mock_response_bad)),
            MagicMock(__enter__=MagicMock(return_value=mock_response_good))
        ]

        meds, conf, latency = self.service.extract_prescription(b"dummy_image_bytes")

        self.assertIsNotNone(meds)
        self.assertEqual(len(meds), 1)
        self.assertEqual(meds[0].medicine_name, "Dolo")

    @patch("urllib.request.urlopen")
    def test_extract_prescription_timeout_or_api_failure(self, mock_urlopen):
        """Test graceful failover on API timeout or error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")

        meds, conf, latency = self.service.extract_prescription(b"dummy_image_bytes")

        self.assertIsNone(meds)
        self.assertEqual(conf, 0.0)


if __name__ == "__main__":
    unittest.main()
