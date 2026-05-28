"""
Router konfigurasi kode akun — CRUD untuk AccountCodeRule.

Endpoint:
  GET    /account-codes                     — daftar semua aturan
  GET    /account-codes/{rule_id}           — satu aturan
  POST   /account-codes                     — buat aturan baru
  PUT    /account-codes/{rule_id}           — update aturan
  DELETE /account-codes/{rule_id}           — hapus aturan
  POST   /account-codes/seed-defaults       — semai ulang default
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..crud import account_code as crud
from ..schemas.account_code import AccountCodeRuleCreate, AccountCodeRuleUpdate, AccountCodeRuleRead

router = APIRouter(
    prefix="/account-codes",
    tags=["Account Codes"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[AccountCodeRuleRead])
def list_rules(db: Session = Depends(get_db)):
    return crud.list_all(db)


@router.get("/{rule_id}", response_model=AccountCodeRuleRead)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = crud.get(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Account code rule not found")
    return rule


@router.post("", response_model=AccountCodeRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(data: AccountCodeRuleCreate, db: Session = Depends(get_db)):
    existing = crud.get_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=409, detail=f"Rule for code '{data.code}' already exists")
    return crud.create(db, data)


@router.put("/{rule_id}", response_model=AccountCodeRuleRead)
def update_rule(rule_id: int, data: AccountCodeRuleUpdate, db: Session = Depends(get_db)):
    rule = crud.get(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Account code rule not found")
    return crud.update(db, rule, data)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = crud.get(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Account code rule not found")
    crud.delete(db, rule)


@router.post("/seed-defaults", status_code=status.HTTP_200_OK)
def seed_defaults(db: Session = Depends(get_db)):
    """
    Hapus semua aturan yang ada lalu semai ulang konfigurasi default.
    Berguna saat reset ke konfigurasi awal.
    """
    crud.delete_all(db)
    inserted = crud.seed_ypii_defaults(db)
    return {"message": f"Seeded {inserted} default account code rules"}
