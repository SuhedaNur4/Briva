from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from app.extensions import db
from app.models.user import User
from app.utils.auth_helpers import get_current_user
from app.utils.validators import parse_request_json, validate_email, validate_password, validate_role
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = parse_request_json(request)
        email = validate_email(data.get('email'))
        password = validate_password(data.get('password'))
        role = validate_role(data.get('role', 'volunteer'))
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    if User.query.filter_by(email=email).first():
        return (jsonify({'error': 'Bu e-posta adresi zaten kayıtlı.'}), 409)
    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return (jsonify({'message': 'Kayıt başarılı.', 'access_token': token, 'user': user.to_dict()}), 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = parse_request_json(request)
        email = validate_email(data.get('email'))
        password = validate_password(data.get('password'))
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return (jsonify({'error': 'E-posta veya parola hatalı.'}), 401)
    if not user.is_active:
        return (jsonify({'error': 'Hesabınız devre dışı. Destek ile iletişime geçin.'}), 403)
    token = create_access_token(identity=str(user.id))
    return (jsonify({'message': 'Giriş başarılı.', 'access_token': token, 'user': user.to_dict()}), 200)

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return (jsonify({'error': 'Kullanıcı bulunamadı.'}), 404)
    return (jsonify({'user': user.to_dict()}), 200)