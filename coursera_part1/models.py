import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

try:
    from .database import Base
except (ImportError, ValueError):
    from database import Base


# ---(Enums)---

# user role for user
class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    manager = "manager"
    admin = "admin"

# user subscription status
class UserSubscriptionStatus(str, enum.Enum):
    free = "free"
    pro = "pro"

# course level for course
class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

# course status
class CourseStatus(str, enum.Enum):
    free = "free"
    plus = "plus"

# study group status
class StudyGroupStatus(str, enum.Enum):
    recruiting = "recruiting"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

# application status for application
class ApplicationStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"

# enrollment status for enrollment
class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"



# class User for users
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(
        Enum(UserRole), default=UserRole.student, nullable=False
    )
    user_status = Column(
        Enum(UserSubscriptionStatus), default=UserSubscriptionStatus.free, nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    teaching_groups = relationship("StudyGroup", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")
    student_applications = relationship(
        "Application", foreign_keys="Application.student_id", back_populates="student"
    )
    managed_applications = relationship(
        "Application", foreign_keys="Application.manager_id", back_populates="manager"
    )


# class category for categories
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), unique=True, nullable=False)

    # relationship
    courses = relationship("Course", back_populates="category")


# class course for courses
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    level = Column(
        Enum(CourseLevel), default=CourseLevel.beginner, nullable=False
    )
    price = Column(Float, default=0.0, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(
        Enum(CourseStatus), default=CourseStatus.free, nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    category = relationship("Category", back_populates="courses")
    study_groups = relationship("StudyGroup", back_populates="course")
    applications = relationship("Application", back_populates="course")


# class study group for groups
class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(155), nullable=False)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=True)

    status = Column(
        Enum(StudyGroupStatus), default=StudyGroupStatus.recruiting, nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    course = relationship("Course", back_populates="study_groups")
    teacher = relationship("User", back_populates="teaching_groups")
    enrollments = relationship("Enrollment", back_populates="group")


# class application for application
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    comment = Column(Text, nullable=True)
    status = Column(
        Enum(ApplicationStatus), default=ApplicationStatus.new, nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationships
    student = relationship(
        "User", foreign_keys=[student_id], back_populates="student_applications"
    )
    manager = relationship(
        "User", foreign_keys=[manager_id], back_populates="managed_applications"
    )
    course = relationship("Course", back_populates="applications")


# class enrollment
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=False)

    status = Column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.active, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    student = relationship("User", back_populates="enrollments")
    group = relationship("StudyGroup", back_populates="enrollments")