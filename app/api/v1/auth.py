from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.auth_service import (
    ManagerUser,
    auth_service,
    get_current_manager,
)

router = APIRouter(prefix="/auth", tags=["Manager Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(..., description="Ім'я користувача менеджера")
    password: str = Field(..., description="Пароль менеджера")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    manager: ManagerUser


class MessageResponse(BaseModel):
    status: str
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Авторизація менеджера та отримання JWT токена доступу."""
    manager = auth_service.authenticate_manager(
        username=credentials.username.strip(),
        password=credentials.password,
    )
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірне ім'я користувача або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(username=manager.username)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        manager=manager,
    )


@router.get("/me", response_model=ManagerUser)
async def get_current_manager_info(
    current_manager: ManagerUser = Depends(get_current_manager),
):
    """Отримати профіль поточного авторизованого менеджера."""
    return current_manager


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_manager: ManagerUser = Depends(get_current_manager),
):
    """Вихід з вебпанелі."""
    return MessageResponse(
        status="success",
        message=f"Користувач {current_manager.username} успішно вийшов із системи",
    )
