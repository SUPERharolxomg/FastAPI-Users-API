from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.security import MAX_PASSWORD_BYTES


def _validate_password_bytes(value: Optional[str]) -> Optional[str]:
    if value is not None and len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"La contraseña no puede superar los {MAX_PASSWORD_BYTES} bytes en UTF-8."
        )
    return value


class UserBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre completo del usuario",
        examples=["Ana García"]
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido e identificador único",
        examples=["ana.garcia@example.com"]
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=MAX_PASSWORD_BYTES,
        description="Contraseña en texto plano (será hasheada en el servicio)",
        examples=["Segura123!"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ana García",
                "email": "ana.garcia@example.com",
                "password": "Segura123!",
            }
        }
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_bytes(value)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nuevo nombre del usuario"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=MAX_PASSWORD_BYTES,
        description="Nueva contraseña si se desea cambiar"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Estado para activar o aplicar borrado lógico"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Ana García Ruiz"}}
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: Optional[str]) -> Optional[str]:
        return _validate_password_bytes(value)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Cuerpo devuelto por la API cuando una petición no se puede completar."""

    detail: str = Field(
        ...,
        description="Mensaje legible que explica el motivo del error",
        examples=["Usuario no encontrado."]
    )
