import os
import io
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from PIL import Image
from app.services.ocr.image_analyzer import analyze_image_quality, ImageQualityAnalysis

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = r"C:\Users\Zoya Ahmed\.gemini\antigravity-ide\brain\e01d9b7f-5d21-49c6-ac2e-416e78b14199\scratch\ocr_debug"


def super_resolution_scale(gray: np.ndarray, scale: int) -> np.ndarray:
    """Stage 2: Super Resolution Upscaling using cv2.INTER_CUBIC."""
    if scale <= 1:
        return gray
    h, w = gray.shape
    return cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)


def auto_deskew(gray: np.ndarray, angle: float) -> np.ndarray:
    """Stage 3: Auto-Deskew & Orientation Correction."""
    if abs(angle) < 0.5:
        return gray
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def remove_shadows(gray: np.ndarray) -> np.ndarray:
    """Stage 5: Background Illumination Estimation & Shadow Removal."""
    dilated = cv2.morphologyEx(gray, cv2.MORPH_DILATE, np.ones((7, 7), np.uint8))
    bg = cv2.medianBlur(dilated, 21)
    diff = 255 - cv2.absdiff(gray, bg)
    norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    return norm


def adaptive_brightness_clahe(gray: np.ndarray) -> np.ndarray:
    """Stage 6: CLAHE Adaptive Histogram Equalization."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def noise_reduction(gray: np.ndarray, is_handwritten: bool) -> np.ndarray:
    """Stage 7: FastNlMeans & Bilateral Denoising while preserving handwritten ink."""
    if is_handwritten:
        return cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)
    return cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)


def unsharp_mask(gray: np.ndarray) -> np.ndarray:
    """Stage 10: Unsharp Masking & Edge Enhancement for blurry text."""
    gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
    return cv2.addWeighted(gray, 1.6, gaussian, -0.6, 0)


def stroke_enhancement(gray: np.ndarray, is_handwritten: bool) -> np.ndarray:
    """Stage 9: Morphological stroke repair & thickening for thin handwritten ink."""
    if not is_handwritten:
        return gray
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    # Morphological closing to bridge broken pen strokes
    closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    return closed


def threshold_otsu(gray: np.ndarray) -> np.ndarray:
    """Stage 8: Otsu Binarization."""
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def threshold_adaptive_gaussian(gray: np.ndarray) -> np.ndarray:
    """Stage 8: Adaptive Gaussian Thresholding."""
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8)


def roi_detection_crop(gray: np.ndarray) -> np.ndarray:
    """Stage 12: Auto-crop ROI prescription region ignoring outer table/phone borders."""
    try:
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return gray
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        if w > 100 and h > 50 and (w * h) > 0.2 * (gray.shape[0] * gray.shape[1]):
            return gray[y:y+h, x:x+w]
    except Exception:
        pass
    return gray


def process_image_adaptive(image_bytes: bytes) -> Tuple[List[Tuple[str, Image.Image]], ImageQualityAnalysis]:
    """
    Intelligent Adaptive Preprocessing Engine:
    1. Analyzes image quality metrics (blur, contrast, brightness, skew, handwriting).
    2. Generates multiple optimized, enhanced variants.
    3. Saves debug stages if DEBUG_OCR is enabled.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        # Fallback for unsupported stream
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    analysis = analyze_image_quality(img_bgr)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Scaling & Deskewing
    scaled = super_resolution_scale(gray, analysis.recommended_scale)
    deskewed = auto_deskew(scaled, analysis.skew_angle) if analysis.has_skew else scaled

    # 2. ROI Crop
    cropped = roi_detection_crop(deskewed)

    # 3. Illumination Correction
    shadow_free = remove_shadows(cropped) if analysis.is_shadowed else cropped

    # 4. CLAHE Adaptive Contrast
    clahe_img = adaptive_brightness_clahe(shadow_free)

    # 5. Denoising / Sharpening
    if analysis.is_blurry:
        sharpened = unsharp_mask(clahe_img)
    else:
        sharpened = noise_reduction(clahe_img, analysis.is_handwritten)

    # 6. Stroke Repair & Threshold Variants
    stroke_enhanced = stroke_enhancement(sharpened, analysis.is_handwritten)
    otsu_variant = threshold_otsu(stroke_enhanced)
    adaptive_variant = threshold_adaptive_gaussian(stroke_enhanced)

    # Build Multi-Version Pipelines (Streamlined for max speed & accuracy)
    variants: List[Tuple[str, np.ndarray]] = [
        ("scaled_gray", scaled),
        ("clahe_enhanced", clahe_img),
        ("stroke_enhanced", stroke_enhanced)
    ]

    # Convert to PIL Image for Tesseract
    pil_variants: List[Tuple[str, Image.Image]] = []
    for name, v_mat in variants:
        pil_variants.append((name, Image.fromarray(v_mat)))

    # Save Debug Mode Output if requested
    if DEBUG_OCR or os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(DEBUG_DIR, "original.png"), img_bgr)
        cv2.imwrite(os.path.join(DEBUG_DIR, "deskewed.png"), deskewed)
        cv2.imwrite(os.path.join(DEBUG_DIR, "shadow_removed.png"), shadow_free)
        cv2.imwrite(os.path.join(DEBUG_DIR, "clahe.png"), clahe_img)
        cv2.imwrite(os.path.join(DEBUG_DIR, "stroke_enhanced.png"), stroke_enhanced)
        cv2.imwrite(os.path.join(DEBUG_DIR, "threshold_otsu.png"), otsu_variant)
        cv2.imwrite(os.path.join(DEBUG_DIR, "final_for_ocr.png"), stroke_enhanced)

    return pil_variants, analysis
