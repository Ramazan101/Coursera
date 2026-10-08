from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

try:
    from . import models, schemas
    from .database import engine, get_db
    from .settings_for_auth import (
        create_access_token,
        get_current_user,
        get_password_hash,
        require_roles,
        verify_password,
    )
except (ImportError, ValueError):
    import models, schemas
    from database import engine, get_db
    from settings_for_auth import (
        create_access_token,
        get_current_user,
        get_password_hash,
        require_roles,
        verify_password,
    )

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coursera API Clone", version="1.0.0")


@app.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        password=get_password_hash(user_data.password),
        role=user_data.role,
        user_status=user_data.user_status,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user



@app.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@app.post(
    "/categories/",
    response_model=schemas.CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.manager))],
)
def create_category(category_data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    if db.query(models.Category).filter(models.Category.category_name == category_data.category_name).first():
        raise HTTPException(status_code=400, detail="Категория с таким именем уже существует")
    category = models.Category(category_name=category_data.category_name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category



@app.get("/courses/", response_model=List[schemas.CourseResponse])
def get_courses(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Course)
    if category_id:
        query = query.filter(models.Course.category_id == category_id)
    return query.all()


@app.get("/courses/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return course


@app.post(
    "/courses/",
    response_model=schemas.CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.teacher))],
)
def create_course(course_data: schemas.CourseCreate, db: Session = Depends(get_db)):
    if not db.query(models.Category).filter(models.Category.id == course_data.category_id).first():
        raise HTTPException(status_code=404, detail="Указанная категория не найдена")

    course = models.Course(**course_data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@app.put(
    "/courses/{course_id}",
    response_model=schemas.CourseResponse,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.teacher))],
)
def update_course(course_id: int, course_data: schemas.CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    for key, value in course_data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)

    db.commit()
    db.refresh(course)
    return course



@app.get("/groups/", response_model=List[schemas.StudyGroupResponse])
def get_groups(db: Session = Depends(get_db)):
    return db.query(models.StudyGroup).all()


@app.post(
    "/groups/",
    response_model=schemas.StudyGroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.manager))],
)
def create_study_group(group_data: schemas.StudyGroupCreate, db: Session = Depends(get_db)):
    if not db.query(models.Course).filter(models.Course.id == group_data.course_id).first():
        raise HTTPException(status_code=404, detail="Курс не найден")
    if not db.query(models.User).filter(models.User.id == group_data.teacher_id).first():
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    group = models.StudyGroup(**group_data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@app.patch(
    "/groups/{group_id}",
    response_model=schemas.StudyGroupResponse,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.manager))],
)
def update_group_status(group_id: int, update_data: schemas.StudyGroupUpdate, db: Session = Depends(get_db)):
    group = db.query(models.StudyGroup).filter(models.StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)
    return group



@app.post("/applications/", response_model=schemas.ApplicationResponse, status_code=status.HTTP_201_CREATED)
def submit_application(
        app_data: schemas.ApplicationCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not db.query(models.Course).filter(models.Course.id == app_data.course_id).first():
        raise HTTPException(status_code=404, detail="Курс не найден")

    application = models.Application(
        student_id=current_user.id,
        course_id=app_data.course_id,
        comment=app_data.comment,
        status=models.ApplicationStatus.new,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.get("/applications/", response_model=List[schemas.ApplicationResponse])
def get_applications(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if current_user.role in [models.UserRole.admin, models.UserRole.manager]:
        return db.query(models.Application).all()
    return db.query(models.Application).filter(models.Application.student_id == current_user.id).all()


@app.patch(
    "/applications/{app_id}/status",
    response_model=schemas.ApplicationResponse,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.manager))],
)
def change_application_status(
        app_id: int,
        status_data: schemas.ApplicationStatusUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    app_obj.status = status_data.status
    app_obj.manager_id = current_user.id
    db.commit()
    db.refresh(app_obj)
    return app_obj



@app.post(
    "/enrollments/",
    response_model=schemas.EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(models.UserRole.admin, models.UserRole.manager))],
)
def enroll_student(enroll_data: schemas.EnrollmentCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == enroll_data.student_id).first():
        raise HTTPException(status_code=404, detail="Студент не найден")
    if not db.query(models.StudyGroup).filter(models.StudyGroup.id == enroll_data.group_id).first():
        raise HTTPException(status_code=404, detail="Группа не найдена")

    enrollment = models.Enrollment(**enroll_data.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@app.get("/enrollments/", response_model=List[schemas.EnrollmentResponse])
def get_enrollments(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if current_user.role in [models.UserRole.admin, models.UserRole.manager]:
        return db.query(models.Enrollment).all()
    return db.query(models.Enrollment).filter(models.Enrollment.student_id == current_user.id).all()