# User Authentication & Role Management with VIT-AP Domain Verification
ALLOWED_EMAIL_DOMAIN = "@vitapstudent.ac.in"

users_db = {
    "siva": {
        "name": "Siva Sathvik",
        "email": "siva.sathvik@vitapstudent.ac.in",
        "password_hash": "password",
        "role": "student"
    },
    "saketh": {
        "name": "Saketh",
        "email": "saketh.k@vitapstudent.ac.in",
        "password_hash": "password",
        "role": "student"
    },
    "shveni": {
        "name": "Shveni",
        "email": "shveni.r@vitapstudent.ac.in",
        "password_hash": "password",
        "role": "student"
    },
    "sahithi": {
        "name": "Sahithi",
        "email": "sahithi.m@vitapstudent.ac.in",
        "password_hash": "password",
        "role": "student"
    },
    "proctor1": {
        "name": "Prof. Smith",
        "email": "proctor@vitapstudent.ac.in",
        "password_hash": "password",
        "role": "proctor"
    }
}

def register_student(name, email, username, password):
    email = email.strip().lower()
    username = username.strip().lower()

    if not email.endswith(ALLOWED_EMAIL_DOMAIN):
        return False, f"Access Denied: Only authorized VIT-AP emails ending with {ALLOWED_EMAIL_DOMAIN} are permitted."

    if username in users_db:
        return False, f"Username '{username}' already exists. Please choose another."

    for u in users_db.values():
        if u.get("email") == email:
            return False, f"An account with email '{email}' already exists."

    users_db[username] = {
        "name": name.strip(),
        "email": email,
        "password_hash": password,
        "role": "student"
    }
    return True, f"Registration successful for {name}! You may now sign in."

def authenticate(login_id, password):
    login_id = login_id.strip().lower()
    for uname, user in users_db.items():
        if uname == login_id or user.get("email") == login_id:
            if user["password_hash"] == password:
                return {
                    "authenticated": True,
                    "username": uname,
                    "role": user["role"],
                    "name": user["name"],
                    "email": user.get("email")
                }
    return {"authenticated": False, "role": None}

def is_proctor(user_session):
    return user_session.get("authenticated") and user_session.get("role") == "proctor"
