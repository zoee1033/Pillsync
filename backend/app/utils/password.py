import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    """
    if not isinstance(password, str):
        password = str(password)

    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain password with the hashed password.
    """
    if not plain_password or not hashed_password:
        return False

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )