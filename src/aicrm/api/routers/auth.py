"""
Маршруты аутентификации
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...models.user import User
from ...services.auth import auth_service
from ...utils.logging import get_logger
from ..schemas.auth import LoginRequest, LoginResponse, Token
from ..schemas.auth import User as UserSchema
from ..schemas.auth import UserRegister

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=UserSchema)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя (только для админов)"""
    # Проверка существования пользователя
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Создание пользователя (админ создает, поэтому сразу активный)
    user_data_dict = user_data.dict()
    user_data_dict["is_active"] = True
    user_data_dict["email_verified"] = (
        True  # Пользователи создаются админом, верификация не нужна
    )

    user = auth_service.create_user(db, user_data_dict)

    logger.info(f"User registered by admin: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Вход в систему"""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Вход в систему (JSON)"""
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/session", response_model=LoginResponse)
async def login_with_session(
    login_data: LoginRequest, request: Request, db: Session = Depends(get_db)
):
    """Вход в систему с созданием сессии"""
    result = await auth_service.login_with_session(
        db, login_data.email, login_data.password, request
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return result


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Выход из системы"""
    try:
        # Извлекаем session_id из токена
        from jose import jwt

        from ...core.config import settings

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        session_id = payload.get("session_id")

        if session_id:
            success = await auth_service.logout_session(session_id)
            if success:
                return {"message": "Successfully logged out"}
            else:
                raise HTTPException(status_code=400, detail="Session not found")
        else:
            # Для обратной совместимости
            return {"message": "Logged out (legacy token)"}

    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/logout/all")
async def logout_all(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Выход из всех сессий"""
    try:
        user = auth_service.get_current_user(db, token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        count = await auth_service.logout_all_sessions(user.id)
        return {"message": f"Logged out from {count} sessions"}

    except Exception as e:
        logger.error("Logout all error", error=str(e))
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Получение текущего пользователя"""
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"


# Note: get_current_active_user and get_current_admin_user are now imported from core.dependencies