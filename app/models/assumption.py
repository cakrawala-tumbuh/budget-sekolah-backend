"""
Model asumsi satuan pendidikan (UnitAssumption).

Menyimpan jumlah siswa per kelas, total siswa baru/lama, jumlah staf,
dan override tarif UP/US serta tarif kegiatan per kelas.
Satu organisasi UNIT memiliki paling banyak satu baris asumsi (relasi 1–1).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UnitAssumption(Base):
    """Student count and rate assumptions for a school unit."""

    __tablename__ = "unit_assumptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), unique=True, nullable=False, index=True
    )

    # Number of students per grade
    grade_1: Mapped[int] = mapped_column(Integer, default=0)
    grade_2: Mapped[int] = mapped_column(Integer, default=0)
    grade_3: Mapped[int] = mapped_column(Integer, default=0)
    grade_4: Mapped[int] = mapped_column(Integer, default=0)
    grade_5: Mapped[int] = mapped_column(Integer, default=0)
    grade_6: Mapped[int] = mapped_column(Integer, default=0)

    # Summary counts
    new_student_count: Mapped[int] = mapped_column(Integer, default=0)
    returning_student_count: Mapped[int] = mapped_column(Integer, default=0)
    staff_count: Mapped[int] = mapped_column(Integer, default=0)

    # Rate overrides (None = auto-calculated from expenses)
    override_up_rate: Mapped[float | None] = mapped_column(Float)
    override_us_rate: Mapped[float | None] = mapped_column(Float)

    # Per-grade activity rate overrides (None = auto from account 5170.01)
    override_activity_grade_1: Mapped[float | None] = mapped_column(Float)
    override_activity_grade_2: Mapped[float | None] = mapped_column(Float)
    override_activity_grade_3: Mapped[float | None] = mapped_column(Float)
    override_activity_grade_4: Mapped[float | None] = mapped_column(Float)
    override_activity_grade_5: Mapped[float | None] = mapped_column(Float)
    override_activity_grade_6: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="assumption"
    )

    @property
    def total_students(self) -> int:
        """Jumlah total siswa dari semua grade slot yang aktif.

        Jika organisasi memiliki GradeConfig, hanya slot hingga num_grades
        yang dijumlahkan. Slot di luar num_grades diasumsikan bernilai 0.
        Jika GradeConfig belum dikonfigurasi, semua 6 slot dijumlahkan.

        Returns:
            Total jumlah siswa aktif.
        """
        grade_values = [
            self.grade_1,
            self.grade_2,
            self.grade_3,
            self.grade_4,
            self.grade_5,
            self.grade_6,
        ]
        num_grades = 6
        if self.organization is not None and self.organization.grade_config is not None:
            num_grades = self.organization.grade_config.num_grades
        return sum(grade_values[:num_grades])
