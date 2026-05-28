"""
Entry point aplikasi FastAPI — Budget Simulator.

Mendaftarkan semua router, mengatur CORS, dan menginisialisasi tabel database
pada saat aplikasi pertama kali dijalankan (lifespan).

Satu instance aplikasi merepresentasikan satu tahun anggaran (BUDGET_YEAR).
Konfigurasi tahun anggaran dibaca dari variabel lingkungan atau file .env.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine, SessionLocal
from .routers import (
    organizations_router,
    assumptions_router,
    grade_configs_router,
    expense_categories_router,
    investment_categories_router,
    income_categories_router,
    budget_entries_router,
    income_entries_router,
    investments_router,
    depreciation_router,
    contributions_router,
    parent_expense_allocations_router,
    simulation_router,
    auth_router,
    users_router,
    database_router,
)
from .crud.income_category import seed_defaults as seed_income_categories
from .crud.investment_category import seed_defaults as seed_investment_categories
from .crud.expense_category import seed_defaults as seed_expense_categories
from .crud.income_category import get_code_to_id_map
from .crud.user import create_or_update_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables at startup (idempotent)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Semai kategori pendapatan terlebih dahulu (diperlukan FK dari ExpenseCategory)
        n_income = seed_income_categories(db)
        if n_income:
            print(f"[startup] Seeded {n_income} default income categories")

        # Semai kategori investasi
        n_invest = seed_investment_categories(db)
        if n_invest:
            print(f"[startup] Seeded {n_invest} default investment categories")

        # Semai kategori biaya (butuh income_code_to_id map untuk FK)
        income_code_to_id = get_code_to_id_map(db)
        n_expense = seed_expense_categories(db, income_code_to_id)
        if n_expense:
            print(f"[startup] Seeded {n_expense} default expense categories")

        # Buat/update akun admin dari env ADMIN_PASSWORD
        create_or_update_admin(db, settings.admin_password)
        print("[startup] Admin user ready (username: admin)")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "API backend simulasi Rencana Anggaran Belanja (RAB). "
        f"Tahun Anggaran: **{settings.budget_year}**."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(database_router)
app.include_router(organizations_router)
app.include_router(assumptions_router)
app.include_router(grade_configs_router)
app.include_router(expense_categories_router)
app.include_router(investment_categories_router)
app.include_router(income_categories_router)
app.include_router(budget_entries_router)
app.include_router(income_entries_router)
app.include_router(investments_router)
app.include_router(depreciation_router)
app.include_router(contributions_router)
app.include_router(parent_expense_allocations_router)
app.include_router(simulation_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.app_name,
        "budget_year": settings.budget_year,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
