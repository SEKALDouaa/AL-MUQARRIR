from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from ..services.user_service import Create_user, Get_user_by_email
from ..schemas.user_schema import UserSchema

user_bp = Blueprint('user', __name__)
user_schema = UserSchema()

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Hash the password before sending to the service
    data['password'] = generate_password_hash(data['password'])

    user = Create_user(data)
    if user is None:
        return jsonify({"message": "User already exists"}), 400

    return jsonify({"message": "User registered successfully"}), 201


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Get_user_by_email(data['email'])

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"message": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token, email=user.email), 200
