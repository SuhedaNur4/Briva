import re
from typing import Any
EMAIL_REGEX = re.compile('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$')
MIN_PASSWORD_LENGTH = 8
MAX_STRING_LENGTH = 255

def validate_email(email: Any) -> str:
    if not email or not isinstance(email, str):
        raise ValueError('E-posta adresi zorunludur.')
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        raise ValueError('Geçerli bir e-posta adresi girin.')
    return email

def validate_password(password: Any) -> str:
    if not password or not isinstance(password, str):
        raise ValueError('Parola zorunludur.')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f'Parola en az {MIN_PASSWORD_LENGTH} karakter olmalıdır.')
    return password

def validate_required_string(value: Any, field_name: str, max_length: int=MAX_STRING_LENGTH) -> str:
    if not value or not isinstance(value, str):
        raise ValueError(f'{field_name} zorunludur.')
    value = value.strip()
    if not value:
        raise ValueError(f'{field_name} boş olamaz.')
    if len(value) > max_length:
        raise ValueError(f'{field_name} en fazla {max_length} karakter olabilir.')
    return value

def validate_optional_string(value: Any, field_name: str, max_length: int=MAX_STRING_LENGTH) -> str | None:
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValueError(f'{field_name} metin olmalıdır.')
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f'{field_name} en fazla {max_length} karakter olabilir.')
    return value

def validate_role(role: Any) -> str:
    allowed_roles = {'volunteer', 'organization'}
    if role not in allowed_roles:
        raise ValueError(f"Geçersiz rol. İzin verilenler: {', '.join(allowed_roles)}")
    return role

def validate_event_status(status: Any) -> str:
    allowed = {'draft', 'published', 'cancelled', 'completed'}
    if status not in allowed:
        raise ValueError(f"Geçersiz etkinlik durumu. İzin verilenler: {', '.join(allowed)}")
    return status

def validate_application_status(status: Any) -> str:
    allowed = {'approved', 'rejected', 'cancelled'}
    if status not in allowed:
        raise ValueError(f"Geçersiz başvuru durumu. İzin verilenler: {', '.join(allowed)}")
    return status

def validate_positive_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} tam sayı olmalıdır.')
    if value <= 0:
        raise ValueError(f'{field_name} pozitif olmalıdır.')
    return value

def parse_request_json(request) -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise ValueError('İstek gövdesi geçerli JSON formatında olmalıdır.')
    return data