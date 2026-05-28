"""
Router kategori pendapatan — CRUD untuk IncomeCategory.

Endpoint:
  GET    /income-categories                  — daftar semua kategori
  GET    /income-categories/{category_id}    — satu kategori
  POST   /income-categories                  — buat kategori baru
  PUT    /income-categories/{category_id}    — update kategori
  DELETE /income-categories/{category_id}    — hapus kategori
  POST   /income-categories/seed-defaults    — semai ulang default YPII
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..crud import income_category as crud
from ..schemas.income_category import (
    IncomeCategoryCreate, IncomeCategoryUpdate, IncomeCategoryRead
)

router = APIRouter(
    prefix="/income-categories",
    tags=["Income Categories"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[IncomeCategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{category_id}", response_model=IncomeCategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Income category not found")
    return cat


@router.post("", response_model=IncomeCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: IncomeCategoryCreate, db: Session = Depends(get_db)):
    existing = crud.get_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category with code '{data.code}' already exists")
    return crud.create(db, data)


@router.put("/{category_id}", response_model=IncomeCategoryRead)
def update_category(category_id: int, data: IncomeCategoryUpdate, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Income category not found")
    return crud.update(db, cat, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Income category not found")
    crud.delete(db, cat)


@router.post("/seed-defaults", status_code=status.HTTP_200_OK)
def seed_defaults(db: Session = Depends(get_db)):
    """Hapus semua kategori pendapatan lalu semai ulang default YPII."""
    crud.delete_all(db)
    inserted = crud.seed_ypii_defaults(db)
    return {"message": f"Seeded {inserted} default YPII income categories"}
