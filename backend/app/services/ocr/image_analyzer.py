import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class ImageQualityAnalysis:
    brightness: float
    contrast: float
    blur_score: float
    shadow_score: float
    skew_angle: float
    is_blurry: bool
    is_low_light: bool
    is_overexposed: bool
    is_low_contrast: bool
    is_shadowed: bool
    is_handwritten: bool
    has_skew: bool
    recommended_scale: int


def analyze_image_quality(img_bgr: np.ndarray) -> ImageQualityAnalysis:
    """
    Analyzes uploaded image quality metrics: blur, brightness, contrast, shadows, skew, and text type.
    """
    if len(img_bgr.shape) == 3:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_bgr.copy()

    h, w = gray.shape

    # 1. Blur Detection (Laplacian Variance)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = blur_score < 100.0

    # 2. Brightness & Contrast
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    is_low_light = brightness < 85.0
    is_overexposed = brightness > 205.0
    is_low_contrast = contrast < 42.0

    # 3. Shadow Detection (Block Illumination Variance)
    block_h, block_w = max(16, h // 8), max(16, w // 8)
    block_means = []
    for r in range(0, h - block_h, block_h):
        for c in range(0, w - block_w, block_w):
            block_means.append(np.mean(gray[r:r+block_h, c:c+block_w]))
    shadow_score = float(np.std(block_means)) if block_means else 0.0
    is_shadowed = shadow_score > 35.0

    # 4. Skew Detection via MinAreaRect
    skew_angle = 0.0
    try:
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) > 50:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.5:
                skew_angle = angle
    except Exception:
        skew_angle = 0.0
    has_skew = abs(skew_angle) > 1.0

    # 5. Handwritten vs Printed Heuristic (Stroke Contour Variance)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contour_areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 5]
    area_std = np.std(contour_areas) if contour_areas else 0.0
    is_handwritten = area_std > 80.0 or blur_score < 180.0

    # 6. Resolution Scaling Recommendation
    if max(w, h) < 1000:
        recommended_scale = 3
    elif max(w, h) < 1800:
        recommended_scale = 2
    else:
        recommended_scale = 1

    return ImageQualityAnalysis(
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        blur_score=round(blur_score, 2),
        shadow_score=round(shadow_score, 2),
        skew_angle=round(skew_angle, 2),
        is_blurry=is_blurry,
        is_low_light=is_low_light,
        is_overexposed=is_overexposed,
        is_low_contrast=is_low_contrast,
        is_shadowed=is_shadowed,
        is_handwritten=is_handwritten,
        has_skew=has_skew,
        recommended_scale=recommended_scale
    )
