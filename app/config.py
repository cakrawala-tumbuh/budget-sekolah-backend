"""
Konfigurasi aplikasi menggunakan pydantic-settings.

Nilai dibaca dari file .env di root proyek atau dari variabel lingkungan sistem.
Seluruh modul mengakses konfigurasi melalui singleton `settings`.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Konfigurasi runtime aplikasi.

    Atribut:
        app_name: Nama aplikasi yang ditampilkan di Swagger UI.
        budget_year: Tahun anggaran format 'YYYY-YYYY', mis. '2025-2026'.
        database_url: URL koneksi SQLAlchemy, default SQLite lokal.
        debug: Mode debug; aktifkan hanya di lingkungan pengembangan.
        admin_password: Password untuk akun admin, wajib diset via env.
        jwt_secret_key: Secret key untuk signing JWT token.
        jwt_expire_minutes: Masa berlaku JWT token dalam menit (default 8 jam).
    """
    app_name: str = "Budget Simulator YPII"
    budget_year: str = "2025-2026"
    database_url: str = "sqlite:///./budget_ypii.db"
    debug: bool = False

    # Auth
    admin_password: str = "admin123"
    jwt_secret_key: str = "changeme-set-this-in-env"
    jwt_expire_minutes: int = 480  # 8 jam

    model_config = {"env_file": ".env"}


settings = Settings()
