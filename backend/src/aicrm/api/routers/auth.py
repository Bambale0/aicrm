"""
Маршруты аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...services.auth import auth_service
from ..schemas.auth import (
    User as UserSchema,
    UserCreate,
    UserRegister,
    EmailVerificationRequest,
    ResendVerificationRequest,
    Token,
    LoginRequest,
    LoginResponse
)
from ...models.user import User
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=UserSchema)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя с верификацией email"""
    # Проверка существования пользователя
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Создание пользователя
    user_data_dict = user_data.dict()
    user_data_dict['email_verified'] = False  # Email не подтвержден при регистрации

    user = auth_service.create_user(db, user_data_dict)

    # Генерация токена верификации
    import secrets
    from datetime import datetime, timedelta

    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)  # Токен действителен 24 часа

    user.email_verification_token = verification_token
    user.email_verification_expires = verification_expires
    db.commit()

    # TODO: Отправка email с верификацией
    # await send_verification_email(user.email, verification_token)

    logger.info(f"User registered: {user.email}, verification token created")
    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
            detail="Incorrect email or password"
        )

    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/session", response_model=LoginResponse)
async def login_with_session(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Вход в систему с созданием сессии"""
    result = await auth_service.login_with_session(db, login_data.email, login_data.password, request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    return result


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Выход из системы"""
    try:
        # Извлекаем session_id из токена
        from jose import jwt
        from ...core.config import settings
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
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
async def logout_all(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Получение текущего пользователя"""
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)):
    """Получение активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: UserSchema = Depends(get_current_user)):
    """Получение активного пользователя с проверкой прав администратора"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Верификация email по токену"""
    user = db.query(User).filter(
        User.email_verification_token == request.token,
        User.email_verification_expires > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    if user.email_verified:
        return {"message": "Email already verified"}

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.commit()

    logger.info(f"User email verified: {user.email}")
    return {"message": "Email successfully verified"}


@router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Повторная отправка письма верификации"""
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        return {"message": "Email already verified"}

    # Генерация нового токена
    import secrets

    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)

    user.email_verification_token = verification_token
    user.email_verification_expires = verification_expires
    db.commit()

    # TODO: Отправка нового email с верификацией
    # await send_verification_email(user.email, verification_token)

    logger.info(f"Verification email resent: {user.email}")
