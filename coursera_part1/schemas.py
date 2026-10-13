from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime, date
from .models import (
    RoleEnum, UserStatusEnum, CourseLevelEnum, CourseStatusEnum,
    StudyGroupStatusEnum, ApplicationStatusEnum, EnrollmentStatusEnum
)


# --- AUTH & USER ---
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.student
    user_status: UserStatusEnum = UserStatusEnum.free
    is_active: bool = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    user_status: UserStatusEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- CATEGORY ---
class CategoryCreate(BaseModel):
    category_name: str


class CategoryOut(CategoryCreate):
    id: int

    class Config:
        from_attributes = True


# --- COURSE ---
class CourseCreate(BaseModel):
    title: str
    category: int
    description: Optional[str] = None
    level: CourseLevelEnum = CourseLevelEnum.beginner
    price: float = 0.0
    duration_weeks: int
    is_active: bool = True
    status: CourseStatusEnum = CourseStatusEnum.free


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[int] = None
    description: Optional[str] = None
    level: Optional[CourseLevelEnum] = None
    price: Optional[float] = None
    duration_weeks: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[CourseStatusEnum] = None


class CourseOut(CourseCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- APPLICATION ---
class ApplicationCreate(BaseModel):
    course_id: int
    comment: Optional[str] = None


class ApplicationUpdateManager(BaseModel):
    status: Optional[ApplicationStatusEnum] = None
    comment: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    manager_id: Optional[int]
    comment: Optional[str]
    status: ApplicationStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- STUDY GROUP & ENROLLMENT ---
class StudyGroupCreate(BaseModel):
    name: str
    course_id: int
    teacher_id: int
    capacity: int = 20
    starts_on: date
    ends_on: date
    status: StudyGroupStatusEnum = StudyGroupStatusEnum.recruiting


class StudyGroupOut(StudyGroupCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    group_id: int


class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    group_id: int
    status: EnrollmentStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


# --- AI AGENT & SEARCH ---
class SearchQuery(BaseModel):
    question: str


class AgentChatRequest(BaseModel):
    message: str


class AgentChatResponse(BaseModel):
    answer: Any
