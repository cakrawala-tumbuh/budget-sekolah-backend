"""
Pydantic schemas untuk konfigurasi grade satuan pendidikan.

GradeConfigCreate/Update digunakan untuk operasi upsert.
grade_N_label bersifat opsional; nilai None berarti label default "Kelas N".
num_grades harus bernilai 1–6.
"""
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GradeConfigBase(BaseModel):
    num_grades: int = Field(default=6, ge=1, le=6)
    grade_1_label: str | None = None
    grade_2_label: str | None = None
    grade_3_label: str | None = None
    grade_4_label: str | None = None
    grade_5_label: str | None = None
    grade_6_label: str | None = None

    @model_validator(mode="after")
    def validate_labels_within_active_range(self) -> "GradeConfigBase":
        """Pastikan label untuk slot di luar num_grades dibiarkan None."""
        for slot in range(self.num_grades + 1, 7):
            if getattr(self, f"grade_{slot}_label") is not None:
                raise ValueError(
                    f"grade_{slot}_label harus None karena num_grades={self.num_grades}"
                )
        return self


class GradeConfigCreate(GradeConfigBase):
    pass


class GradeConfigUpdate(GradeConfigBase):
    pass


class GradeSlotRead(BaseModel):
    """Representasi satu slot grade yang aktif, lengkap dengan label efektif."""

    slot: int
    label: str

    model_config = {"from_attributes": True}


class GradeConfigRead(GradeConfigBase):
    id: int
    organization_id: int
    active_grades: list[GradeSlotRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_labels(cls, obj: object) -> "GradeConfigRead":
        """Buat GradeConfigRead dari ORM object, termasuk active_grades.

        Args:
            obj: Instance GradeConfig ORM.

        Returns:
            GradeConfigRead yang sudah diisi active_grades.
        """
        data = {
            "id": obj.id,
            "organization_id": obj.organization_id,
            "num_grades": obj.num_grades,
            "grade_1_label": obj.grade_1_label,
            "grade_2_label": obj.grade_2_label,
            "grade_3_label": obj.grade_3_label,
            "grade_4_label": obj.grade_4_label,
            "grade_5_label": obj.grade_5_label,
            "grade_6_label": obj.grade_6_label,
            "active_grades": [
                GradeSlotRead(slot=i, label=obj.get_label(i))
                for i in range(1, obj.num_grades + 1)
            ],
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return cls.model_validate(data)
