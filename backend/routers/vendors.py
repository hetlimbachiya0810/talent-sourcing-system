from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from db.database import get_async_session
from models.models import Vendor
from schemas import VendorCreate, VendorResponse

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new vendor entry.
    - **name**: Vendor's name (required)
    - **email**: Vendor's email (optional)
    - **contact**: Vendor's contact number (optional)
    """
    try:
        db_vendor = Vendor(
            name=vendor.name,
            email=vendor.email,
            contact=vendor.contact
        )
        db.add(db_vendor)
        await db.commit()
        await db.refresh(db_vendor)
        return db_vendor
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating vendor: {str(e)}"
        )

@router.get("/", response_model=List[VendorResponse])
async def get_all_vendors(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all vendors.
    """
    try:
        result = await db.execute(select(Vendor))
        vendors = result.scalars().all()
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vendors: {str(e)}"
        )