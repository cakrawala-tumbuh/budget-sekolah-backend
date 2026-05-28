"""
Pydantic schemas untuk asumsi satuan pendidikan.

UnitAssumptionCreate/Update digunakan untuk operasi upsert.
Override tarif UP/US dan tarif kegiatan per kelas bersifat opsional;
nilai None berarti tarif dihitung otomatis dari simulasi biaya.
"""
from datetime import datetime

from pydantic import BaseModel, model_validator


class UnitAssumptionBase(BaseModel):
    grade_1: int = 0
    grade_2: int = 0
    grade_3: int = 0
    grade_4: int = 0
    grade_5: int = 0
    grade_6: int = 0
    new_student_count: int = 0
    returning_student_count: int = 0
    staff_count: int = 0
    override_up_rate: float | None = None
    override_us_rate: float | None = None
    override_activity_grade_1: float | None = None
    override_activity_grade_2: float | None = None
    override_activity_grade_3: float | None = None
    override_activity_grade_4: float | None = None
    override_activity_grade_5: float | None = None
    override_activity_grade_6: float | None = None

    @model_validator(mode="after")
    def validate_counts(self) -> "UnitAssumptionBase":
        for field in ("grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6",
                      "new_student_count", "returning_student_count", "staff_count"):
            if getattr(self, field) < 0:
                raise ValueError(f"{field} must not be negative")
        return self


class UnitAssumptionCreate(UnitAssumptionBase):
    pass


class UnitAssumptionUpdate(UnitAssumptionBase):
    pass


class UnitAssumptionRead(UnitAssumptionBase):
    id: int
    organization_id: int
    total_students: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
