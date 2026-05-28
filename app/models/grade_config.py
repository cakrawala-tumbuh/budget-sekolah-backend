"""
Model konfigurasi tingkat kelas (GradeConfig) per satuan pendidikan.

Setiap UNIT dapat memiliki konfigurasi grade yang berbeda:
- num_grades: jumlah grade aktif (1–6)
- grade_N_label: nama tampilan untuk tiap slot grade

Contoh:
  - SD  : num_grades=6, label "Kelas 1"–"Kelas 6"
  - SMP : num_grades=3, label "Kelas 7"–"Kelas 9"
  - SMA : num_grades=3, label "Kelas 10"–"Kelas 12"
  - TK  : num_grades=2, label "TK A", "TK B"
  - KB/Daycare: num_grades=3, label "Toddler", "Playgroup", "TK"

Slot grade yang tidak aktif (> num_grades) tidak ditampilkan ke pengguna
dan nilainya di UnitAssumption harus dibiarkan 0.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GradeConfig(Base):
    """Grade slot configuration for a school unit organisation."""

    __tablename__ = "grade_configs"
    __table_args__ = (
        CheckConstraint("num_grades BETWEEN 1 AND 6", name="ck_grade_configs_num_grades"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), unique=True, nullable=False, index=True
    )

    # How many of the six grade slots are active for this school
    num_grades: Mapped[int] = mapped_column(Integer, default=6)

    # Display labels for each grade slot (None = use default "Kelas N")
    grade_1_label: Mapped[str | None] = mapped_column(String(50))
    grade_2_label: Mapped[str | None] = mapped_column(String(50))
    grade_3_label: Mapped[str | None] = mapped_column(String(50))
    grade_4_label: Mapped[str | None] = mapped_column(String(50))
    grade_5_label: Mapped[str | None] = mapped_column(String(50))
    grade_6_label: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="grade_config"
    )

    def get_label(self, slot: int) -> str:
        """Return the display label for a grade slot (1-indexed).

        Args:
            slot: Grade slot number (1–6).

        Returns:
            Custom label if set, otherwise "Kelas {slot}".

        Raises:
            ValueError: If slot is outside 1–6.
        """
        if not 1 <= slot <= 6:
            raise ValueError(f"Grade slot must be between 1 and 6, got {slot}")
        raw = getattr(self, f"grade_{slot}_label")
        return raw if raw is not None else f"Kelas {slot}"

    @property
    def active_labels(self) -> list[str]:
        """Return display labels for all active grade slots (length == num_grades).

        Returns:
            List of label strings, one per active grade slot.
        """
        return [self.get_label(i) for i in range(1, self.num_grades + 1)]
