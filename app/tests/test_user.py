"""
Suite de tests de la API de usuarios.

Organizada en las tres categorías que documenta el README: camino feliz,
casos de error y casos límite.
"""

import pytest

from app.models.user import User
from app.utils.security import (
    MAX_PASSWORD_BYTES,
    hash_password,
    verify_password,
)


# --------------------------------------------------------------------------
# Camino feliz
# --------------------------------------------------------------------------

def test_health_check_responde_ok(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "API activa y respondiendo",
    }


def test_crear_usuario_devuelve_201(client, user_payload):
    response = client.post("/users/", json=user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == user_payload["name"]
    assert body["email"] == user_payload["email"]
    assert body["is_active"] is True
    assert isinstance(body["id"], int)
    assert body["created_at"] and body["updated_at"]


def test_la_contrasena_nunca_viaja_en_la_respuesta(client, user_payload):
    body = client.post("/users/", json=user_payload).json()

    assert "password" not in body


def test_la_contrasena_se_guarda_hasheada(client, db_session, user_payload):
    client.post("/users/", json=user_payload)

    user = db_session.query(User).filter(User.email == user_payload["email"]).one()
    assert user.password != user_payload["password"]
    assert user.password.startswith("$2b$")
    assert verify_password(user_payload["password"], user.password)


def test_obtener_usuario_por_id(client, created_user):
    response = client.get("/users/{}".format(created_user["id"]))

    assert response.status_code == 200
    assert response.json() == created_user


def test_listar_usuarios_devuelve_los_activos(client, user_payload):
    for i in range(3):
        payload = {**user_payload, "email": "user{}@example.com".format(i)}
        client.post("/users/", json=payload)

    response = client.get("/users/")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_listar_usuarios_respeta_la_paginacion(client, user_payload):
    for i in range(5):
        payload = {**user_payload, "email": "user{}@example.com".format(i)}
        client.post("/users/", json=payload)

    primera = client.get("/users/?skip=0&limit=2").json()
    segunda = client.get("/users/?skip=2&limit=2").json()

    assert len(primera) == 2
    assert len(segunda) == 2
    # Las páginas no se solapan.
    assert {u["id"] for u in primera}.isdisjoint({u["id"] for u in segunda})


def test_patch_actualiza_solo_lo_enviado(client, created_user):
    response = client.patch(
        "/users/{}".format(created_user["id"]),
        json={"name": "Ana Ruiz"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ana Ruiz"
    # El email no se tocó.
    assert body["email"] == created_user["email"]


def test_patch_refresca_updated_at(client, created_user):
    body = client.patch(
        "/users/{}".format(created_user["id"]),
        json={"name": "Ana Ruiz"},
    ).json()

    assert body["updated_at"] > created_user["updated_at"]
    assert body["created_at"] == created_user["created_at"]


def test_patch_de_contrasena_se_rehashea(client, db_session, created_user):
    response = client.patch(
        "/users/{}".format(created_user["id"]),
        json={"password": "NuevaClave456!"},
    )

    assert response.status_code == 200
    user = db_session.query(User).filter(User.id == created_user["id"]).one()
    assert verify_password("NuevaClave456!", user.password)


def test_delete_devuelve_204_y_desactiva(client, db_session, created_user):
    response = client.delete("/users/{}".format(created_user["id"]))

    assert response.status_code == 204
    assert response.content == b""

    user = db_session.query(User).filter(User.id == created_user["id"]).one()
    # Borrado lógico: la fila sigue existiendo, sólo cambia el flag.
    assert user.is_active is False


# --------------------------------------------------------------------------
# Casos de error
# --------------------------------------------------------------------------

def test_email_duplicado_devuelve_409(client, user_payload, created_user):
    response = client.post("/users/", json=user_payload)

    assert response.status_code == 409
    assert "detail" in response.json()


def test_email_duplicado_tambien_si_el_usuario_esta_inactivo(
    client, user_payload, created_user
):
    client.delete("/users/{}".format(created_user["id"]))

    response = client.post("/users/", json=user_payload)

    # El email sigue ocupado por la fila inactiva: la unicidad es a nivel de BD.
    assert response.status_code == 409


def test_obtener_usuario_inexistente_devuelve_404(client):
    response = client.get("/users/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado."


def test_obtener_usuario_inactivo_devuelve_404(client, created_user):
    client.delete("/users/{}".format(created_user["id"]))

    response = client.get("/users/{}".format(created_user["id"]))

    assert response.status_code == 404


def test_patch_sobre_usuario_inexistente_devuelve_404(client):
    response = client.patch("/users/9999", json={"name": "Nadie"})

    assert response.status_code == 404


def test_borrar_dos_veces_devuelve_404(client, created_user):
    assert client.delete("/users/{}".format(created_user["id"])).status_code == 204

    response = client.delete("/users/{}".format(created_user["id"]))

    assert response.status_code == 404


@pytest.mark.parametrize("campo_ausente", ["name", "email", "password"])
def test_payload_incompleto_devuelve_422(client, user_payload, campo_ausente):
    payload = {k: v for k, v in user_payload.items() if k != campo_ausente}

    response = client.post("/users/", json=payload)

    assert response.status_code == 422


# --------------------------------------------------------------------------
# Casos límite
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "email_invalido",
    ["sin-arroba", "@example.com", "ana@", "ana @example.com", ""],
)
def test_email_con_formato_invalido_devuelve_422(
    client, user_payload, email_invalido
):
    response = client.post(
        "/users/",
        json={**user_payload, "email": email_invalido},
    )

    assert response.status_code == 422


def test_contrasena_corta_devuelve_422(client, user_payload):
    response = client.post(
        "/users/",
        json={**user_payload, "password": "corta"},
    )

    assert response.status_code == 422


def test_nombre_demasiado_corto_devuelve_422(client, user_payload):
    response = client.post("/users/", json={**user_payload, "name": "A"})

    assert response.status_code == 422


def test_contrasena_de_mas_de_72_caracteres_devuelve_422(client, user_payload):
    response = client.post(
        "/users/",
        json={**user_payload, "password": "a" * 100},
    )

    assert response.status_code == 422


def test_contrasena_multibyte_que_excede_72_bytes_devuelve_422(
    client, user_payload
):
    """
    Regresión: 72 caracteres acentuados pasan el límite de longitud de Pydantic
    (que cuenta caracteres) pero son 144 bytes en UTF-8, y bcrypt sólo admite
    72 bytes. Debe rechazarse con 422, nunca reventar con un 500.
    """
    response = client.post(
        "/users/",
        json={**user_payload, "password": "á" * 72},
    )

    assert response.status_code == 422


def test_contrasena_justo_en_el_limite_de_72_bytes_se_acepta(
    client, user_payload
):
    response = client.post(
        "/users/",
        json={**user_payload, "password": "a" * MAX_PASSWORD_BYTES},
    )

    assert response.status_code == 201


def test_patch_no_permite_cambiar_el_email(client, created_user):
    response = client.patch(
        "/users/{}".format(created_user["id"]),
        json={"email": "otro@example.com"},
    )

    assert response.status_code == 200
    # El campo extra se ignora en lugar de aplicarse.
    assert response.json()["email"] == created_user["email"]


def test_patch_no_permite_falsear_created_at(client, created_user):
    response = client.patch(
        "/users/{}".format(created_user["id"]),
        json={"created_at": "1999-01-01T00:00:00Z"},
    )

    assert response.status_code == 200
    assert response.json()["created_at"] == created_user["created_at"]


def test_usuario_borrado_no_aparece_en_el_listado(client, user_payload):
    activo = client.post(
        "/users/",
        json={**user_payload, "email": "activo@example.com"},
    ).json()
    borrado = client.post(
        "/users/",
        json={**user_payload, "email": "borrado@example.com"},
    ).json()
    client.delete("/users/{}".format(borrado["id"]))

    listado = client.get("/users/").json()

    ids = [u["id"] for u in listado]
    assert activo["id"] in ids
    assert borrado["id"] not in ids


@pytest.mark.parametrize("limit_invalido", [0, -1, 500])
def test_limit_fuera_de_rango_devuelve_422(client, limit_invalido):
    response = client.get("/users/?limit={}".format(limit_invalido))

    assert response.status_code == 422


def test_skip_negativo_devuelve_422(client):
    response = client.get("/users/?skip=-1")

    assert response.status_code == 422


# --------------------------------------------------------------------------
# Módulo de seguridad
# --------------------------------------------------------------------------

def test_hash_password_genera_salt_distinto_cada_vez():
    primero = hash_password("Segura123!")
    segundo = hash_password("Segura123!")

    assert primero != segundo
    assert verify_password("Segura123!", primero)
    assert verify_password("Segura123!", segundo)


def test_verify_password_rechaza_la_contrasena_incorrecta():
    hashed = hash_password("Segura123!")

    assert verify_password("Incorrecta999", hashed) is False


def test_verify_password_no_revienta_con_un_hash_corrupto():
    assert verify_password("Segura123!", "esto-no-es-un-hash") is False


def test_hash_password_rechaza_mas_de_72_bytes():
    with pytest.raises(ValueError):
        hash_password("á" * 73)
