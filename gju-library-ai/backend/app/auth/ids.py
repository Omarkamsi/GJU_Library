import hashlib
import hmac


def hash_email(email: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode(), email.strip().lower().encode(), hashlib.sha256
    ).hexdigest()


def email_domain(email: str) -> str:
    if "@" not in email:
        raise ValueError("not an email")
    return email.split("@", 1)[1].strip().lower()
