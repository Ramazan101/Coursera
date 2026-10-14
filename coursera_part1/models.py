import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Date, Enum, Text
)
from sqlalchemy.orm import relationship
from .database import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    manager = "manager"
    admin = "admin"


class UserStatusEnum(str, enum.Enum):
    free = "free"
    pro = "pro"


class CourseLevelEnum(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class CourseStatusEnum(str, enum.Enum):
    free = "free"
    plus = "plus"


class StudyGroupStatusEnum(str, enum.Enum):
    recruiting = "recruiting"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ApplicationStatusEnum(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class EnrollmentStatusEnum(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    user_status = Column(Enum(UserStatusEnum), default=UserStatusEnum.free, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True, nullable=False)
    courses = relationship("Course", back_populates="category_rel")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    category = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Enum(CourseLevelEnum), default=CourseLevelEnum.beginner, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(CourseStatusEnum), default=CourseStatusEnum.free, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_rel = relationship("Category", back_populates="courses")


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    capacity = Column(Integer, default=20, nullable=False)
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=False)
    status = Column(Enum(StudyGroupStatusEnum), default=StudyGroupStatusEnum.recruiting, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="group")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.new, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=False)
    status = Column(Enum(EnrollmentStatusEnum), default=EnrollmentStatusEnum.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("StudyGroup", back_populates="enrollments")