from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes.user import router as user_router


TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Comprobación del estado del servicio.",
    },
    {
        "name": "Users",
        "description": (
            "Gestión de usuarios: alta, consulta, actualización parcial y "
            "baja lógica."
        ),
    },
]

DESCRIPTION = """
API RESTful de gestión de usuarios construida con **FastAPI**, **SQLAlchemy**
y **PostgreSQL**.

### Comportamiento a tener en cuenta

* **Borrado lógico**: `DELETE` marca al usuario como inactivo (`is_active=False`)
  en lugar de eliminar la fila. Los usuarios inactivos dejan de aparecer en las
  consultas.
* **Contraseñas**: se almacenan hasheadas con bcrypt y nunca se devuelven en las
  respuestas. El máximo son 72 bytes en UTF-8, que es el límite del algoritmo:
  ojo, se miden en bytes, así que las tildes y emojis ocupan más de un carácter.
* **Email único**: dar de alta un correo ya registrado devuelve `409 Conflict`.

### Documentación

* **Swagger UI**: [/docs](/docs)
* **ReDoc**: [/redoc](/redoc)
* **Esquema OpenAPI**: [/openapi.json](/openapi.json)
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="API de Gestión de Usuarios",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Harold David Garces Casas"},
    servers=[{"url": "http://localhost:8000", "description": "Entorno local"}],
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)


@app.get(
    "/",
    tags=["Health"],
    summary="Estado del servicio",
    response_description="El servicio está activo",
)
def health_check():
    """Devuelve `200` si la API está en marcha. Útil como healthcheck."""
    return {"status": "ok", "message": "API activa y respondiendo"}
