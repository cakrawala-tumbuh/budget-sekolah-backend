"""
Router kategori investasi — CRUD untuk InvestmentCategory.

Endpoint:
  GET    /investment-categories                  — daftar semua kategori
  GET    /investment-categories/{category_id}    — satu kategori
  POST   /investment-categories                  — buat kategori baru
  PUT    /investment-categories/{category_id}    — update kategori
  DELETE /investment-categories/{category_id}    — hapus kategori
  POST   /investment-categories/seed-defaults    — semai ulang default YPII
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..crud import investment_category as crud
from ..schemas.investment_category import (
    InvestmentCategoryCreate, InvestmentCategoryUpdate, InvestmentCategoryRead
)

router = APIRouter(
    prefix="/investment-categories",
    tags=["Investment Categories"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[InvestmentCategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{category_id}", response_model=InvestmentCategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Investment category not found")
    return cat


@router.post("", response_model=InvestmentCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: InvestmentCategoryCreate, db: Session = Depends(get_db)):
    existing = crud.get_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category with code '{data.code}' already exists")
    return crud.create(db, data)


@router.put("/{category_id}", response_model=InvestmentCategoryRead)
def update_category(category_id: int, data: InvestmentCategoryUpdate, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Investment category not found")
    return crud.update(db, cat, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Investment category not found")
    crud.delete(db, cat)


@router.post("/seed-defaults", status_code=status.HTTP_200_OK)
def seed_defaults(db: Session = Depends(get_db)):
    """Hapus semua kategori investasi lalu semai ulang default YPII."""
    crud.delete_all(db)
    inserted = crud.seed_ypii_defaults(db)
    return {"message": f"Seeded {inserted} default YPII investment categories"}
