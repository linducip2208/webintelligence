from ..core.security import hash_password, verify_password, new_token

SESSIONS: dict = {}


def create_user(email, password):
    return {"email": email, "password_hash": hash_password(password)}


def login(users: dict, email: str, password: str):
    u = users.get(email)
    if not u or not verify_password(password, u["password_hash"]):
        return None
    t = new_token()
    SESSIONS[t] = email
    return t


def check(tok):
    return SESSIONS.get(tok)
