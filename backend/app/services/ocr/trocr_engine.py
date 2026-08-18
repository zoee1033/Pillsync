"""
Microsoft TrOCR Engine for PillSync OCR Pipeline.

This module provides an OCR engine utilizing Microsoft's TrOCR (Transformer OCR)
handwritten model ('microsoft/trocr-base-handwritten') for recognizing handwritten
prescriptions and medical notes.

Features:
- Single-instance (singleton) model loading to avoid redundant memory usage.
- Auto-detection and support for both CPU and CUDA execution.
- Direct conversion of OpenCV (numpy array BGR/GRAY) images to PIL Images.
- Extraction of predicted text and token sequence confidence scores.
- Comprehensive logging and robust error handling.
"""

import logging
import time
import threading
from typing import Tuple, Dict, Any, Optional, Union
import numpy as np
from PIL import Image

# Configure module logger
logger = logging.getLogger(__name__)

# Optional / Lazy imports for PyTorch and Transformers
try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    F = None
    TORCH_AVAILABLE = False
    logger.warning("PyTorch ('torch') is not installed. TrOCR engine will require PyTorch to run inference.")

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TrOCRProcessor = None
    VisionEncoderDecoderModel = None
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Hugging Face 'transformers' is not installed. TrOCR engine will require 'transformers' to run inference.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    logger.warning("OpenCV ('cv2') is not installed. OpenCV image conversions will use fallback methods.")


DEFAULT_MODEL_NAME = "microsoft/trocr-base-handwritten"


def convert_opencv_to_pil(image: Union[np.ndarray, Image.Image]) -> Image.Image:
    """
    Converts an OpenCV image (numpy ndarray in BGR, BGRA, or Grayscale) to a PIL RGB Image.
    
    Args:
        image: OpenCV image array or PIL Image.
        
    Returns:
        PIL.Image.Image: Converted PIL RGB Image.
        
    Raises:
        ValueError: If input image is empty or invalid format.
    """
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    
    if not isinstance(image, np.ndarray):
        raise ValueError(f"Unsupported image type '{type(image)}'. Expected numpy.ndarray or PIL.Image.Image.")
    
    if image.size == 0 or image.ndim < 2:
        raise ValueError("Provided numpy array image is empty or invalid.")

    # Handle grayscale image (H, W) or (H, W, 1)
    if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
        if image.ndim == 3:
            image = image.squeeze(axis=2)
        if CV2_AVAILABLE:
            rgb_arr = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb_arr = np.stack([image] * 3, axis=-1)
        return Image.fromarray(rgb_arr, mode="RGB")
    
    # Handle 3-channel BGR image (H, W, 3)
    elif image.ndim == 3 and image.shape[2] == 3:
        if CV2_AVAILABLE:
            rgb_arr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            # Fallback manual channel swap BGR -> RGB
            rgb_arr = image[:, :, ::-1]
        return Image.fromarray(rgb_arr, mode="RGB")
    
    # Handle 4-channel BGRA image (H, W, 4)
    elif image.ndim == 3 and image.shape[2] == 4:
        if CV2_AVAILABLE:
            rgb_arr = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            rgb_arr = image[:, :, [2, 1, 0]]
        return Image.fromarray(rgb_arr, mode="RGB")
    
    else:
        raise ValueError(f"Unsupported image array shape: {image.shape}")


class TrOCREngine:
    """
    Singleton TrOCR Engine for handwritten OCR inference using Hugging Face Transformers.
    
    Ensures model and processor are loaded only once in memory across the application lifecycle.
    """
    _instance: Optional["TrOCREngine"] = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: Optional[str] = None):
        """
        Private/Internal constructor. Use TrOCREngine.get_instance() or run_trocr() instead.
        """
        self.model_name = model_name
        self.requested_device = device
        self.device: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.model: Optional[Any] = None
        self._is_loaded = False
        self._load_lock = threading.Lock()

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME, device: Optional[str] = None) -> "TrOCREngine":
        """
        Returns the singleton instance of TrOCREngine, creating it if it does not exist.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_name=model_name, device=device)
        return cls._instance

    def _determine_device(self) -> Any:
        """
        Determines and validates the execution device (CPU or CUDA).
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required to run TrOCR. Please install 'torch'.")

        if self.requested_device:
            target_device = self.requested_device.lower()
            if "cuda" in target_device:
                if torch.cuda.is_available():
                    return torch.device(target_device)
                else:
                    logger.warning(f"Requested device '{self.requested_device}' but CUDA is not available. Falling back to CPU.")
                    return torch.device("cpu")
            return torch.device(target_device)
        
        # Auto-detect CUDA vs CPU
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "CUDA"
            logger.info(f"CUDA detected. Using GPU device: {device_name}")
            return torch.device("cuda")
        else:
            logger.info("CUDA not available. Initializing TrOCR on CPU.")
            return torch.device("cpu")

    def load_model(self) -> None:
        """
        Loads the TrOCR processor and model into memory once.
        Thread-safe method.
        """
        if self._is_loaded:
            return

        with self._load_lock:
            if self._is_loaded:
                return

            if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
                missing = []
                if not TORCH_AVAILABLE:
                    missing.append("torch")
                if not TRANSFORMERS_AVAILABLE:
                    missing.append("transformers")
                err_msg = f"Cannot load TrOCR model. Missing required packages: {', '.join(missing)}"
                logger.error(err_msg)
                raise ImportError(err_msg)

            logger.info(f"Loading TrOCR model '{self.model_name}' (this may take a moment on first run)...")
            start_time = time.time()

            try:
                self.device = self._determine_device()
                
                # Load processor and model
                self.processor = TrOCRProcessor.from_pretrained(self.model_name)
                self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
                
                # Transfer model to targeted device and set to evaluation mode
                self.model.to(self.device)
                self.model.eval()

                self._is_loaded = True
                elapsed = time.time() - start_time
                logger.info(f"TrOCR model '{self.model_name}' successfully loaded on device [{self.device}] in {elapsed:.2f}s.")

            except Exception as e:
                logger.error(f"Failed to load TrOCR model '{self.model_name}': {e}", exc_info=True)
                raise RuntimeError(f"TrOCR model initialization failed: {e}") from e

    def predict(self, image: Union[np.ndarray, Image.Image]) -> Tuple[str, float]:
        """
        Performs OCR text recognition on an input OpenCV image or PIL Image.
        
        Args:
            image: OpenCV numpy array (BGR/GRAY) or PIL Image.
            
        Returns:
            Tuple[str, float]: A tuple containing:
                - text (str): The recognized text extracted from the image.
                - confidence (float): Sequence confidence score between 0.0 and 100.0.
        """
        res = self.extract_text_with_details(image)
        return res["text"], res["confidence"]

    def extract_text_with_details(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Performs OCR text recognition and returns full inference metadata.
        
        Args:
            image: OpenCV numpy array (BGR/GRAY) or PIL Image.
            
        Returns:
            Dict[str, Any]: Dictionary containing 'text', 'confidence', 'inference_time_ms', 'engine', 'device'.
        """
        start_time = time.time()

        # Ensure model is loaded (loads only once)
        if not self._is_loaded:
            self.load_model()

        # Convert OpenCV -> PIL RGB Image
        try:
            pil_img = convert_opencv_to_pil(image)
        except Exception as conv_err:
            logger.error(f"Image conversion failed in TrOCR engine: {conv_err}")
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "TrOCR_Base_Handwritten",
                "inference_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(conv_err)
            }

        try:
            # Prepare pixel values for model
            pixel_values = self.processor(images=pil_img, return_tensors="pt").pixel_values.to(self.device)

            # Perform generation with score output for confidence calculation
            with torch.no_grad():
                outputs = self.model.generate(
                    pixel_values,
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_new_tokens=128
                )

            # Decode generated token IDs to text
            generated_ids = outputs.sequences
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

            # Calculate confidence score from token generation probabilities
            confidence = self._compute_confidence(outputs)

            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(
                f"[TrOCR] Recognized text: '{generated_text[:60]}' | "
                f"Confidence: {confidence:.2f}% | "
                f"Time: {elapsed_ms}ms | Device: {self.device}"
            )

            return {
                "text": generated_text,
                "confidence": round(confidence, 2),
                "engine": "TrOCR_Base_Handwritten",
                "inference_time_ms": elapsed_ms,
                "device": str(self.device)
            }

        except Exception as infer_err:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"[TrOCR] Inference failed: {infer_err}", exc_info=True)
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "TrOCR_Base_Handwritten_Error",
                "inference_time_ms": elapsed_ms,
                "error": str(infer_err)
            }

    def _compute_confidence(self, outputs: Any) -> float:
        """
        Computes the average sequence confidence score (percentage 0.0 to 100.0)
        from generation output scores.
        """
        if not hasattr(outputs, "scores") or not outputs.scores:
            return 0.0

        try:
            scores = outputs.scores  # Tuple of step tensors, each shape (1, vocab_size)
            sequences = outputs.sequences[0]  # Tensor of shape (seq_len,)

            num_steps = len(scores)
            if num_steps == 0 or len(sequences) < num_steps:
                return 0.0

            # Step tokens correspond to the last num_steps tokens in sequences
            gen_tokens = sequences[-num_steps:]
            step_probabilities = []

            for i, step_scores in enumerate(scores):
                token_id = gen_tokens[i]
                # Apply softmax over vocabulary logits
                probs = F.softmax(step_scores[0], dim=-1)
                token_prob = probs[token_id].item()
                step_probabilities.append(token_prob)

            if not step_probabilities:
                return 0.0

            # Average probability across generated tokens as percentage (0 - 100%)
            mean_prob = float(np.mean(step_probabilities))
            return mean_prob * 100.0

        except Exception as conf_err:
            logger.warning(f"[TrOCR] Failed to calculate sequence confidence: {conf_err}")
            return 0.0


# Module-level convenience functions
def get_trocr_engine(model_name: str = DEFAULT_MODEL_NAME, device: Optional[str] = None) -> TrOCREngine:
    """
    Gets or initializes the singleton TrOCR engine instance.
    """
    return TrOCREngine.get_instance(model_name=model_name, device=device)


def run_trocr(image: Union[np.ndarray, Image.Image], device: Optional[str] = None) -> Tuple[str, float]:
    """
    Top-level helper function to run TrOCR recognition on an OpenCV or PIL image.
    
    Args:
        image: OpenCV numpy image array (BGR/GRAY) or PIL Image.
        device: Optional device string ('cpu', 'cuda', etc.).
        
    Returns:
        Tuple[str, float]: (recognized_text, confidence_percentage)
    """
    engine = get_trocr_engine(device=device)
    return engine.predict(image)
