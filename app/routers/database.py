"""
Router manajemen database.

Endpoint (semua memerlukan role ADMIN):
  POST /database/create   — Reset database: hapus semua data, buat ulang tabel, seed ulang default
  GET  /database/backup   — Unduh file backup database SQLite
  POST /database/restore  — Upload file backup SQLite untuk memulihkan database
"""
import io
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from ..auth import require_admin
from ..config import settings
from ..crud.expense_category import seed_defaults as seed_expense_categories
from ..crud.income_category import get_code_to_id_map
from ..crud.income_category import seed_defaults as seed_income_categories
from ..crud.investment_category import seed_defaults as seed_investment_categories
from ..crud.user import create_or_update_admin
from ..database import Base, SessionLocal, engine
from ..models.user import User

router = APIRouter(prefix="/database", tags=["Database"])

_SQLITE_MAGIC = b"SQLite format 3\x00"


def _get_db_path() -> Path:
    """
    Dapatkan path absolut file database SQLite dari URL engine.

    Returns:
        Path absolut file database.

    Raises:
        HTTPException 400: Jika database bukan file SQLite (mis. in-memory).
    """
    db = engine.url.database
    if not db or db == ":memory:":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operasi tidak didukung untuk database in-memory",
        )
    return Path(db).resolve()


@router.post("/create", summary="Reset database ke kondisi awal")
def create_new_database(current_user: User = Depends(require_admin)):
    """
    Hapus seluruh data dan buat ulang database dari awal.

    Semua tabel dihapus lalu dibuat ulang, kemudian data default (kategori pendapatan,
    kategori investasi, kategori biaya, dan akun admin) disemai kembali.

    **PERHATIAN**: Operasi ini tidak dapat dibatalkan. Semua data akan hilang.

    Args:
        current_user: User admin yang sedang login.

    Returns:
        Jumlah data default yang disemai.
    """
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        n_income = seed_income_categories(db)
        n_invest = seed_investment_categories(db)
        income_code_to_id = get_code_to_id_map(db)
        n_expense = seed_expense_categories(db, income_code_to_id)
        create_or_update_admin(db, settings.admin_password)
    finally:
        db.close()

    return {
        "message": "Database baru berhasil dibuat. Semua data lama telah dihapus.",
        "seeded": {
            "income_categories": n_income,
            "investment_categories": n_invest,
            "expense_categories": n_expense,
        },
    }


@router.get("/backup", summary="Unduh backup database")
def backup_database(current_user: User = Depends(require_admin)):
    """
    Buat dan unduh backup file database SQLite.

    Backup dibuat menggunakan SQLite Online Backup API sehingga aman dilakukan
    saat database sedang aktif digunakan.

    Args:
        current_user: User admin yang sedang login.

    Returns:
        File backup database (.db) sebagai attachment.
    """
    db_path = _get_db_path()
    if not db_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File database tidak ditemukan",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_budget_{timestamp}.db"

    try:
        buf = io.BytesIO()
        source_conn = sqlite3.connect(str(db_path))
        dest_conn = sqlite3.connect(":memory:")
        try:
            source_conn.backup(dest_conn)
        finally:
            source_conn.close()

        # Tulis memory DB ke bytes buffer melalui file sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp_path = tmp.name
        try:
            disk_conn = sqlite3.connect(tmp_path)
            dest_conn.backup(disk_conn)
            disk_conn.close()
            dest_conn.close()
            with open(tmp_path, "rb") as f:
                buf.write(f.read())
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat backup: {exc}",
        ) from exc

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", summary="Pulihkan database dari file backup")
def restore_database(
    file: UploadFile = File(..., description="File backup SQLite (.db)"),
    current_user: User = Depends(require_admin),
):
    """
    Pulihkan database dari file backup SQLite yang diunggah.

    File yang diunggah divalidasi terlebih dahulu (magic bytes SQLite), kemudian
    disalin ke database aktif menggunakan SQLite Online Backup API.

    **PERHATIAN**: Semua data saat ini akan digantikan oleh isi file backup.

    Args:
        file: File backup SQLite (.db).
        current_user: User admin yang sedang login.

    Returns:
        Pesan konfirmasi.

    Raises:
        HTTPException 400: File bukan SQLite yang valid.
        HTTPException 500: Kesalahan saat proses restore.
    """
    content = file.file.read()

    if not content.startswith(_SQLITE_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File tidak valid: bukan database SQLite (magic bytes tidak cocok)",
        )

    db_path = _get_db_path()
    tmp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        engine.dispose()

        source_conn = sqlite3.connect(tmp_path)
        dest_conn = sqlite3.connect(str(db_path))
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            source_conn.close()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memulihkan database: {exc}",
        ) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"message": "Database berhasil dipulihkan dari file backup"}
