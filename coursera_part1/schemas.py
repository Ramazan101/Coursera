from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
try:
    from .models import (
        UserRole,
        UserSubscriptionStatus,
        CourseLevel,
        CourseStatus,
        StudyGroupStatus,
        ApplicationStatus,
        EnrollmentStatus,
    )
except (ImportError, ValueError):
    from models import (
        UserRole,
        UserSubscriptionStatus,
        CourseLevel,
        CourseStatus,
        StudyGroupStatus,
        ApplicationStatus,
        EnrollmentStatus,
    )


class UserProfileOutput(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    password: str = Field(gt=4, lt=12)
    role: UserRole
    user_status: UserSubscriptionStatus
    create_at: datetime
    update_at: datetime

class UserProfileInput(BaseModel):
    full_name: str