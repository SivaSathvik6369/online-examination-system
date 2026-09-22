# User Authentication & Role Management
users_db = {
    "siva": {"password_hash": "hash_siva", "role": "student", "name": "Siva Sathvik"},
    "saketh": {"password_hash": "hash_saketh", "role": "student", "name": "Saketh"},
    "shveni": {"password_hash": "hash_shveni", "role": "student", "name": "Shveni"},
    "sahithi": {"password_hash": "hash_sahithi", "role": "student", "name": "Sahithi"},
    "proctor1": {"password_hash": "hash_proctor", "role": "proctor", "name": "Prof. Smith"}
}

def authenticate(username, password_hash):
    user = users_db.get(username)
    if user and user["password_hash"] == password_hash:
        return {"authenticated": True, "username": username, "role": user["role"], "name": user["name"]}
    return {"authenticated": False, "role": None}

def is_proctor(user_session):
    return user_session.get("authenticated") and user_session.get("role") == "proctor"
