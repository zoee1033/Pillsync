import os
import io
import logging
from typing import Dict, Any, List
import cv2
import numpy as np
from PIL import Image
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.ocr_schema import OCRExtractResponse
from app.services.ocr_service import extract_prescription_data

logger = logging.getLogger(__name__)

# Configurable upload limits loaded at startup
MAX_UPLOAD_SIZE_MB: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10"))
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}


async def validate_and_read_image(file: UploadFile) -> bytes:
    """
    Validates uploaded file against security, content type, max file size (10 MB),
    empty file detection, and image stream corruption checks.
    
    Raises:
        HTTPException: 400 (Empty), 413 (File Too Large), 415 (Unsupported Media Type), 422 (Corrupt Image)
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided in upload request."
        )

    # 1. Content Type Check
    if file.content_type and not file.content_type.startswith("image/") and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{file.content_type}'. Allowed image formats: JPEG, PNG, WebP."
        )

    # 2. Read bytes and check length
    image_bytes = await file.read()
    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty (0 bytes)."
        )

    # 3. Max Upload Size Check (10 MB)
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded image size ({len(image_bytes) / (1024*1024):.2f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB} MB."
        )

    # 4. Decodability & Corruption Check via OpenCV & PIL
    nparr = np.frombuffer(image_bytes, np.uint8)
    decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if decoded_img is None:
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img.verify()
        except Exception as e:
            logger.warning(f"[OCR_ROUTE] Failed to decode image stream: {e}")
            raise HTTPException(
                status_code=422,
                detail="Corrupted or unreadable image file stream."
            )

    return image_bytes


router = APIRouter(
    prefix="/ocr",
    tags=["OCR Recognition"]
)


@router.post(
    "/upload",
    response_model=OCRExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Prescription Image",
    description="Upload a handwritten or printed prescription image for AI-driven OCR extraction and validation.",
    response_description="Structured prescription details containing medicine names, dosages, frequencies, and confidence metrics.",
    responses={
        400: {"description": "Empty file or missing upload parameter."},
        413: {"description": "Upload size exceeds maximum allowed threshold (10 MB)."},
        415: {"description": "Unsupported file MIME type."},
        422: {"description": "Corrupted or undecodable image stream."}
    }
)
async def upload_prescription_image(
    file: UploadFile = File(..., description="Prescription or medicine strip image file (JPEG, PNG, WebP)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> OCRExtractResponse:
    """
    Uploads prescription image and executes OpenCV + Tesseract + Gemini Vision verification pipeline.
    """
    image_bytes = await validate_and_read_image(file)
    result = extract_prescription_data(image_bytes, filename=file.filename or "")
    return result


@router.post(
    "/extract",
    response_model=OCRExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Prescription Details",
    description="Direct extraction endpoint for prescription image analysis.",
    response_description="Extracted prescription details model.",
    responses={
        400: {"description": "Empty file or missing upload parameter."},
        413: {"description": "Upload size exceeds maximum allowed threshold (10 MB)."},
        415: {"description": "Unsupported file MIME type."},
        422: {"description": "Corrupted or undecodable image stream."}
    }
)
async def extract_prescription(
    file: UploadFile = File(..., description="Prescription image file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> OCRExtractResponse:
    """
    Direct extraction route for prescription recognition.
    """
    image_bytes = await validate_and_read_image(file)
    result = extract_prescription_data(image_bytes, filename=file.filename or "")
    return result
