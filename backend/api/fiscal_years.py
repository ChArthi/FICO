"""
Fiscal Year Variant & Posting Periods API Router.
"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.fico_models import Company, FiscalYear
from backend.schemas.fico_schemas import FiscalYearCreate, FiscalYearResponse
from backend.core.security import oauth2_scheme

router = APIRouter(prefix="/api/fiscal-years", tags=["Fiscal Year"])

def parse_fiscal_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%d-%m-%Y").date()

@router.get(
    "/",
    response_model=List[FiscalYearResponse],
    summary="List Fiscal Years"
)
def get_fiscal_years(db: Session = Depends(get_db)):
    """Retrieve all configured fiscal year variants and statuses."""
    return db.query(FiscalYear).order_by(FiscalYear.id.asc()).all()

@router.post(
    "/",
    response_model=FiscalYearResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Fiscal Year"
)
def create_fiscal_year(
    fy: FiscalYearCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    """Register a new fiscal year period."""
    company_id = fy.company_id
    if company_id is None:
        company_id = db.query(Company.id).order_by(Company.id.asc()).limit(1).scalar()
    elif db.query(Company.id).filter(Company.id == company_id).first() is None:
        available_ids = [row[0] for row in db.query(Company.id).order_by(Company.id.asc()).all()]
        raise HTTPException(
            status_code=404,
            detail=(
                f"Company ID {company_id} not found. Available company IDs: {available_ids}. "
                "Use an available ID or omit company_id to use the first company."
            ),
        )
    if company_id is None:
        raise HTTPException(status_code=400, detail="Create a company before adding a fiscal year.")

    existing = db.query(FiscalYear).filter(
        FiscalYear.company_id == company_id,
        FiscalYear.year == fy.year
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Fiscal Year already exists.")

    values = fy.model_dump()
    values["company_id"] = company_id
    values["start_date"] = parse_fiscal_date(fy.start_date)
    values["end_date"] = parse_fiscal_date(fy.end_date)
    new_fy = FiscalYear(**values)
    db.add(new_fy)
    db.commit()
    db.refresh(new_fy)
    return new_fy
