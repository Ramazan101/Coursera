from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

try:
    from .models import (
        ApplicationStatus,
        CourseLevel,
        CourseStatus,
        EnrollmentStatus,
        StudyGroupStatus,
        UserRole,
        UserSubscriptionStatus,
    )
except (ImportError, ValueError):
    from models import (
        ApplicationStatus,
        CourseLevel,
        CourseStatus,
        EnrollmentStatus,
        StudyGroupStatus,
        UserRole,
        UserSubscriptionStatus,
    )


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Auth
class Token(BaseSchema):
    access_token: str
    token_type: str


class TokenData(BaseSchema):
    email: Optional[str] = None


# User
class UserCreate(BaseSchema):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.student
    user_status: Optional[UserSubscriptionStatus] = UserSubscriptionStatus.free


class UserResponse(BaseSchema):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    user_status: UserSubscriptionStatus
    created_at: datetime
    updated_at: datetime


# Category
class CategoryBase(BaseSchema):
    category_name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int


# Course
class CourseBase(BaseSchema):
    title: str
    description: str
    category_id: int
    level: Optional[CourseLevel] = CourseLevel.beginner
    price: Optional[float] = 0.0
    duration_weeks: int
    is_active: Optional[bool] = True
    status: Optional[CourseStatus] = CourseStatus.free


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    level: Optional[CourseLevel] = None
    price: Optional[float] = None
    duration_weeks: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[CourseStatus] = None


class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime


# Study Group
class StudyGroupBase(BaseSchema):
    name: str
    course_id: int
    teacher_id: int
    starts_on: date
    ends_on: Optional[date] = None
    status: Optional[StudyGroupStatus] = StudyGroupStatus.recruiting


class StudyGroupCreate(StudyGroupBase):
    pass


class StudyGroupUpdate(BaseSchema):
    name: Optional[str] = None
    starts_on: Optional[date] = None
    ends_on: Optional[date] = None
    status: Optional[StudyGroupStatus] = None


class StudyGroupResponse(StudyGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime


# Application
class ApplicationCreate(BaseSchema):
    course_id: int
    comment: Optional[str] = None


class ApplicationStatusUpdate(BaseSchema):
    status: ApplicationStatus


class ApplicationResponse(BaseSchema):
    id: int
    student_id: int
    course_id: int
    manager_id: Optional[int] = None
    comment: Optional[str] = None
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


# Enrollment
class EnrollmentCreate(BaseSchema):
    student_id: int
    group_id: int
    status: Optional[EnrollmentStatus] = EnrollmentStatus.active


class EnrollmentResponse(BaseSchema):
    id: int
    student_id: int
    group_id: int
    status: EnrollmentStatus
    created_at: datetime