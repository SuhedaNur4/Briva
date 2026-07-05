from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def get_current_user() -> User | None:
    try:
        user_id = get_jwt_identity()
        return User.query.get(int(user_id))
    except Exception:
        return None

def role_required(*roles: str):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user:
                return (jsonify({'error': 'Kullanıcı bulunamadı'}), 404)
            if not user.is_active:
                return (jsonify({'error': 'Hesap devre dışı'}), 403)
            if user.role not in roles:
                return (jsonify({'error': 'Bu işlem için yetkiniz yok', 'required_roles': list(roles)}), 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def volunteer_required(fn):
    return role_required('volunteer')(fn)

def organization_required(fn):
    return role_required('organization')(fn)

def admin_required(fn):
    return role_required('admin')(fn)