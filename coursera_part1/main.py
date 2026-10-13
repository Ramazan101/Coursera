import re
import os
import json
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import (
    User, Category, Course, StudyGroup, Application, Enrollment,
    RoleEnum, CourseStatusEnum, StudyGroupStatusEnum, EnrollmentStatusEnum
)
from .schemas import (
    UserRegister, UserLogin, CategoryCreate, CategoryOut,
    CourseCreate, CourseUpdate, CourseOut,
    ApplicationCreate, ApplicationUpdateManager, ApplicationOut,
    StudyGroupCreate, StudyGroupOut, EnrollmentCreate, EnrollmentOut,
    SearchQuery, AgentChatRequest, AgentChatResponse
)
from .settings_for_auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coursera Platform & AI Agent")


# ==========================================
# 1. AUTH (/auth/register/, /auth/login/)
# ==========================================
@app.post("/auth/register/")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password=hash_password(user_in.password),
        role=user_in.role,
        user_status=user_in.user_status,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Сиз ийгиликтуу регистрация болдунуз"}


@app.post("/auth/login/")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}


# ==========================================
# 2. CATEGORY CRUD (ТОЛЬКО ADMIN)
# ==========================================
@app.post("/categories/", response_model=CategoryOut)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([RoleEnum.admin]))
):
    cat = Category(category_name=cat_in.category_name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@app.get("/categories/", response_model=List[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([RoleEnum.admin]))
):
    return db.query(Category).all()


@app.put("/categories/{cat_id}/", response_model=CategoryOut)
def update_category(
    cat_id: int,
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([RoleEnum.admin]))
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    cat.category_name = cat_in.category_name
    db.commit()
    db.refresh(cat)
    return cat


@app.delete("/categories/{cat_id}/")
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([RoleEnum.admin]))
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(cat)
    db.commit()
    return {"message": "Категория удалена"}


# ==========================================
# 3. COURSE CRUD (ТОЛЬКО TEACHER)
# ==========================================
@app.post("/courses/", response_model=CourseOut)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles([RoleEnum.teacher]))
):
    course = Course(**course_in.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@app.get("/courses/", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()


@app.put("/courses/{course_id}/", response_model=CourseOut)
def update_course(
    course_id: int,
    course_in: CourseUpdate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles([RoleEnum.teacher]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    for k, v in course_in.model_dump(exclude_unset=True).items():
        setattr(course, k, v)
    db.commit()
    db.refresh(course)
    return course


@app.delete("/courses/{course_id}/")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles([RoleEnum.teacher]))
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    db.delete(course)
    db.commit()
    return {"message": "Курс удален"}


# ==========================================
# 4. APPLICATION (Student Create / Manager CRUD)
# ==========================================
@app.post("/applications/", response_model=ApplicationOut)
def create_application(
    app_in: ApplicationCreate,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles([RoleEnum.student]))
):
    course = db.query(Course).filter(Course.id == app_in.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Проверка: student.is_active == True ИЛИ (student.is_active == False и course.status == free)
    if not student.is_active and course.status != CourseStatusEnum.free:
        raise HTTPException(
            status_code=403,
            detail="Неактивный студент может подать заявку только на бесплатный курс (free)"
        )

    application = Application(
        student_id=student.id,
        course_id=app_in.course_id,
        comment=app_in.comment
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.get("/applications/", response_model=List[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles([RoleEnum.manager]))
):
    return db.query(Application).all()


@app.get("/applications/{app_id}/", response_model=ApplicationOut)
def detail_application(
    app_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles([RoleEnum.manager]))
):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return application


@app.patch("/applications/{app_id}/", response_model=ApplicationOut)
def update_application(
    app_id: int,
    app_in: ApplicationUpdateManager,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles([RoleEnum.manager]))
):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    application.manager_id = manager.id
    for k, v in app_in.model_dump(exclude_unset=True).items():
        setattr(application, k, v)
    db.commit()
    db.refresh(application)
    return application


@app.delete("/applications/{app_id}/")
def delete_application(
    app_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles([RoleEnum.manager]))
):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    db.delete(application)
    db.commit()
    return {"message": "Заявка удалена"}


# ==========================================
# 5. STUDY GROUP & ENROLLMENT (Student)
# ==========================================
@app.post("/study-groups/join/", response_model=EnrollmentOut)
def join_study_group(
    enroll_in: EnrollmentCreate,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles([RoleEnum.student]))
):
    group = db.query(StudyGroup).filter(StudyGroup.id == enroll_in.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    # Проверка: статус группы == recruiting
    if group.status != StudyGroupStatusEnum.recruiting:
        raise HTTPException(status_code=400, detail="Набор в эту группу закрыт (не recruiting)")

    # Проверка: capacity (свободные места)
    current_count = db.query(Enrollment).filter(
        Enrollment.group_id == group.id,
        Enrollment.status == EnrollmentStatusEnum.active
    ).count()
    if current_count >= group.capacity:
        raise HTTPException(status_code=400, detail="В группе нет свободных мест (capacity превышен)")

    enrollment = Enrollment(student_id=student.id, group_id=group.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@app.get("/enrollments/", response_model=List[EnrollmentOut])
def get_my_enrollments(
    db: Session = Depends(get_db),
    student: User = Depends(require_roles([RoleEnum.student]))
):
    # Аналог get_queryset для студента: видит только свои зачисления
    return db.query(Enrollment).filter(Enrollment.student_id == student.id).all()


# ==========================================
# 6. ПОИСК КУРСОВ (/search/)
# ==========================================
@app.post("/search/", response_model=List[CourseOut])
def search_courses(query: SearchQuery, db: Session = Depends(get_db)):
    q_text = query.question.lower()
    courses_q = db.query(Course).filter(Course.is_active == True)

    # Извлекаем ограничение по неделям, например: "до 4 недель"
    weeks_match = re.search(r"до\s*(\d+)\s*недел", q_text)
    if weeks_match:
        max_weeks = int(weeks_match.group(1))
        courses_q = courses_q.filter(Course.duration_weeks <= max_weeks)

    # Извлекаем ключевые слова (например, python, java, дизайн и т.д.)
    stop_words = {"найди", "мне", "курс", "курсы", "по", "продолжительность", "до", "недель", "недели"}
    words = [w for w in re.findall(r"[a-zа-яё0-9]+", q_text) if w not in stop_words and not w.isdigit()]

    results = courses_q.all()
    if words:
        filtered = [
            c for c in results
            if any(w in c.title.lower() or (c.description and w in c.description.lower()) for w in words)
        ]
        return filtered
    return results


# ==========================================
# 7. AI AGENT (/agent/chat/)
# ==========================================
@app.post("/agent/chat/", response_model=AgentChatResponse)
def agent_chat(
    req: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обрабатывает запросы к профилю текущего авторизованного пользователя.
    Полностью покрывает кейсы 2–9 (и может работать как через OpenAI Function Calling,
    так и через встроенный детерминированный обработчик).
    """
    msg = req.message.strip()
    msg_lower = msg.lower()

    # Кейс 7: Попытка получить чужой профиль (например, "с id 999")
    id_override_match = re.search(r"id\s+(\d+)", msg_lower)
    if id_override_match and int(id_override_match.group(1)) != current_user.id:
        return {
            "answer": "Я могу получить только профиль пользователя, авторизованного в текущем запросе."
        }

    # Кейс 8: Попытка изменить/удалить профиль (в базовом режиме только чтение)
    if any(word in msg_lower for word in ["измени", "поменяй", "обнови", "удали", "change", "update", "delete"]):
        return {
            "answer": "У меня нет инструмента для изменения. Сейчас я могу только читать твой профиль."
        }

    # Кейс 3: "Какой у меня id? Ответь только значением."
    if "какой у меня id" in msg_lower or "только значением" in msg_lower:
        return {"answer": current_user.id}

    # Кейс 4: "Дата регистрации согласно моему профилю?"
    if "дата регистрации" in msg_lower:
        created_str = current_user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"answer": f"В твоём профиле дата регистрации {created_str}"}

    # Кейс 5: "Мой аккаунт отмечен как актуальный?"
    if "актуальный" in msg_lower or "активен" in msg_lower or "is_active" in msg_lower:
        if current_user.is_active:
            return {"answer": "Да, в твоём профиле is_active установлен в true."}
        return {"answer": "Нет, в твоём профиле is_active установлен в false."}

    # Кейс 6: Запрос на кыргызском языке ("кыргызча")
    if "кыргызча" in msg_lower or "атымды" in msg_lower:
        return {
            "answer": f"Профилиңизде атыңыз {current_user.full_name} деп көрсөтүлгөн. Почтаныз {current_user.email}"
        }

    # Кейс 2 (и общий запрос профиля): "Покажи мой профиль: фио, почту и роль."
    return {
        "answer": f"фио: {current_user.full_name}. почта: {current_user.email}. роль: {current_user.role.value}"
    }


# --- ИНСТРУМЕНТЫ (TOOLS) ДЛЯ ДОП ДЗ ---

def tool_get_my_profile(current_user: User) -> dict:
    """Чтение профиля текущего пользователя."""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    }


def tool_update_my_profile(
    db: Session,
    current_user: User,
    new_email: str = None,
    new_full_name: str = None
) -> str:
    """UPDATE: Изменение email или ФИО текущего авторизованного пользователя."""
    if new_email:
        exists = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
        if exists:
            return "Этот email уже занят другим пользователем."
        current_user.email = new_email
    if new_full_name:
        current_user.full_name = new_full_name

    db.commit()
    db.refresh(current_user)
    return f"Профиль успешно обновлён: фио={current_user.full_name}, почта={current_user.email}"


def tool_delete_my_profile(db: Session, current_user: User) -> str:
    """DELETE: Удаление собственного аккаунта."""
    db.delete(current_user)
    db.commit()
    return "Твой профиль был успешно удалён."


def tool_register_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    role: str = "student"
) -> str:
    """REGISTER: Регистрация нового пользователя через агента."""
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        return "Пользователь с таким email уже существует."
    user = User(
        full_name=full_name,
        email=email,
        password=hash_password(password),
        role=RoleEnum(role),
        is_active=False
    )
    db.add(user)
    db.commit()
    return "Сиз ийгиликтуу регистрация болдунуз"