from ..models.user import User
from ..extensions import db

def Create_user(data):
    User = User(**data)
    db.session.add(User)
    db.session.commit()
    return User

def Get_user_by_email(user_email):
    user = User.query.get(user_email)
    if not user:
        return None
    return user

def Get_all_users():
    users = User.query.all()
    if not users:
        return None
    return users