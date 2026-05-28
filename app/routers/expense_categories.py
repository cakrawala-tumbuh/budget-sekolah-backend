"""
Router kategori biaya — CRUD untuk ExpenseCategory.

Endpoint:
  GET    /expense-categories                  — daftar semua kategori
  GET    /expense-categories/{category_id}    — satu kategori
  POST   /expense-categories                  — buat kategori baru
  PUT    /expense-categories/{category_id}    — update kategori
  DELETE /expense-categories/{category_id}    — hapus kategori
  POST   /expense-categories/seed-defaults    — semai ulang default
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..crud import expense_category as crud, income_category as income_crud
from ..schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryRead

router = APIRouter(
    prefix="/expense-categories",
    tags=["Expense Categories"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[ExpenseCategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{category_id}", response_model=ExpenseCategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Expense category not found")
    return cat


@router.post("", response_model=ExpenseCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: ExpenseCategoryCreate, db: Session = Depends(get_db)):
    existing = crud.get_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category with code '{data.code}' already exists")
    return crud.create(db, data)


@router.put("/{category_id}", response_model=ExpenseCategoryRead)
def update_category(category_id: int, data: ExpenseCategoryUpdate, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Expense category not found")
    return crud.update(db, cat, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = crud.get(db, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Expense category not found")
    crud.delete(db, cat)


@router.post("/seed-defaults", status_code=status.HTTP_200_OK)
def seed_defaults(db: Session = Depends(get_db)):
    """Hapus semua kategori biaya lalu semai ulang default."""
    crud.delete_all(db)
    income_code_to_id = income_crud.get_code_to_id_map(db)
    inserted = crud.seed_defaults(db, income_code_to_id)
    return {"message": f"Seeded {inserted} default expense categories"}
