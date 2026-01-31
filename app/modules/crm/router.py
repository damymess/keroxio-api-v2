"""
CRM module - customer/lead management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.crm.models import Lead, Contact

router = APIRouter()


# Schemas
class LeadCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    status: str
    source: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContactCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Lead endpoints
@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lead (public endpoint for landing pages)"""
    # Check if lead already exists
    result = await db.execute(select(Lead).where(Lead.email == lead_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        return existing  # Return existing lead instead of error
    
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all leads (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = select(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(limit)
    if status:
        query = query.where(Lead.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/leads/{lead_id}")
async def update_lead_status(
    lead_id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update lead status"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = status
    await db.commit()
    return {"message": "Lead updated", "status": status}


# Contact endpoints
@router.post("/contacts", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact"""
    contact = Contact(**contact_data.model_dump(), owner_id=current_user["id"])
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's contacts"""
    query = select(Contact).where(
        Contact.owner_id == current_user["id"]
    ).order_by(Contact.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_crm_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get CRM statistics"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count leads by status
    result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .group_by(Lead.status)
    )
    lead_stats = {row[0]: row[1] for row in result.all()}
    
    # Total contacts
    result = await db.execute(select(func.count(Contact.id)))
    total_contacts = result.scalar()
    
    return {
        "leads": lead_stats,
        "total_contacts": total_contacts
    }
