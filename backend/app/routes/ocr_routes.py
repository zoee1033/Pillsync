from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.ocr_schema import OCRExtractResponse
from app.services.ocr_service import extract_prescription_data

router = APIRouter(
    prefix="/ocr",
    tags=["OCR Recognition"]
)


@router.post(
    "/upload",
    response_model=OCRExtractResponse,
    status_code=status.HTTP_200_OK
)
async def upload_prescription_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a prescription or medicine strip image to run OCR extraction.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image format (JPEG, PNG, WEBP)."
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is empty."
        )

    result = extract_prescription_data(image_bytes, filename=file.filename or "")
    return result


@router.post(
    "/extract",
    response_model=OCRExtractResponse,
    status_code=status.HTTP_200_OK
)
async def extract_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract medicine details from an uploaded prescription image.
    """
    image_bytes = await file.read()
    result = extract_prescription_data(image_bytes, filename=file.filename or "")
    return result
