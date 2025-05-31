from flask import Blueprint, request, jsonify
from ..services.user_service import Create_user, Get_user_by_email, Get_all_users
from ..schemas.user_schema import UserSchema

user_bp = Blueprint('user', __name__)

user_shema = UserSchema()
users_shema = UserSchema(many=True)

@user_bp.route('/users', methods=['POST'])
def create():
    data = request.get_json()
    user = Create_user(data)
    if user is None:
        return jsonify({"message": "Email already exists"}), 400
    return user_shema.jsonify(user), 201

@user_bp.route('/users/<string:user_email>', methods=['GET'])
def get_user(user_email):
    user = Get_user_by_email(user_email)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return user_shema.jsonify(user)

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    users = Get_all_users()
    if not users:
        return jsonify({"message": "No users found"}), 404
    return users_shema.jsonify(users)