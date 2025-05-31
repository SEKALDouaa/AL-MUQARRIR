from ..models.user import User
from ..extensions import db
from datetime import datetime

def Create_user(data):
    existing_user = User.query.filter_by(email=data.get('email')).first()
    if existing_user:
        return None
    
    if 'dateNaissance' in data:
        data['dateNaissance'] = datetime.strptime(data['dateNaissance'], "%Y-%m-%d").date()

    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return user

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