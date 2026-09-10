from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import ErrorResponse, UserCreate, UserResponse, UserUpdate
from app.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "No existe un usuario activo con ese ID",
    }
}


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    response_description="Usuario creado correctamente",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El correo electrónico ya está registrado",
        }
    },
)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Da de alta un usuario.

    La contraseña se hashea con bcrypt antes de guardarla y nunca se devuelve
    en la respuesta. El correo debe ser único entre todos los usuarios,
    incluidos los que están inactivos.
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya se encuentra registrado."
        )

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password=hash_password(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get(
    "/",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios activos",
    response_description="Listado de usuarios activos",
)
def list_users(
    skip: int = Query(
        0,
        ge=0,
        description="Número de registros a omitir (paginación)"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
        description="Número máximo de registros a devolver"
    ),
    db: Session = Depends(get_db)
):
    """
    Devuelve los usuarios activos, paginados.

    Los usuarios dados de baja (`is_active=False`) quedan excluidos.
    """
    users = (
        db.query(User)
        .filter(User.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un usuario por ID",
    response_description="Usuario encontrado",
    responses=NOT_FOUND_RESPONSE,
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Recupera un usuario activo por su ID."""
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente un usuario",
    response_description="Usuario actualizado",
    responses=NOT_FOUND_RESPONSE,
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza sólo los campos enviados en el cuerpo; el resto se deja intacto.

    Si se incluye `password`, se hashea antes de guardarla. El correo
    electrónico no se puede modificar por esta vía.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar usuario (borrado lógico)",
    response_description="Usuario desactivado; no devuelve contenido",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "No existe un usuario activo con ese ID",
        }
    },
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Aplica un borrado lógico: marca al usuario como inactivo en lugar de
    eliminar la fila, de modo que se conserva el histórico.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o ya inactivo."
        )

    user.is_active = False
    db.commit()
    return None
