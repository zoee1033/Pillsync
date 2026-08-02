from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.analytics_service import get_adherence_analytics, get_dashboard_summary

router = APIRouter(
    tags=["Analytics"]
)


@router.get(
    "/analytics",
    status_code=status.HTTP_200_OK
)
def fetch_full_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive, on-demand PostgreSQL medication adherence analytics.
    """
    return get_adherence_analytics(db=db, current_user=current_user)


@router.get(
    "/analytics/adherence",
    status_code=status.HTTP_200_OK
)
def fetch_adherence_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get medication adherence analytics and streak summaries.
    """
    return get_adherence_analytics(db=db, current_user=current_user)


@router.get(
    "/dashboard/summary",
    status_code=status.HTTP_200_OK
)
def fetch_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time Dashboard summary cards strictly calculated from PostgreSQL database.
    """
    return get_dashboard_summary(db=db, current_user=current_user)
