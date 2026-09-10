import bcrypt

# bcrypt solo procesa los primeros 72 bytes de la contraseña; superarlos es un error.
MAX_PASSWORD_BYTES = 72


def _encode(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"La contraseña no puede superar los {MAX_PASSWORD_BYTES} bytes."
        )
    return password_bytes


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _encode(plain_password),
            hashed_password.encode("utf-8")
        )
    except ValueError:
        return False
