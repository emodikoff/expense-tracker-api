from app.security import hash_password, verify_password

def test_hashed_password():
    password = "MySecurePassword1234"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


def test_verify_password():
    password = "MySecurePassword1234"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_hash_password_uses_random_salt():
    password = "MySecurePassword1234"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash

    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True