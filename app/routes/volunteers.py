from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.volunteer import VolunteerProfile
from app.utils.auth_helpers import get_current_user, volunteer_required
from app.utils.validators import parse_request_json, validate_required_string, validate_optional_string
volunteers_bp = Blueprint('volunteers', __name__)

@volunteers_bp.route('/me', methods=['GET'])
@jwt_required()
@volunteer_required
def get_my_profile():
    user = get_current_user()
    profile = user.volunteer_profile
    if not profile:
        return (jsonify({'error': 'Profil henüz oluşturulmamış.', 'hint': 'PUT /api/volunteers/me ile profil oluşturun.'}), 404)
    return (jsonify({'volunteer': profile.to_dict()}), 200)

@volunteers_bp.route('/me', methods=['PUT'])
@jwt_required()
@volunteer_required
def upsert_my_profile():
    user = get_current_user()
    profile = user.volunteer_profile
    is_new = profile is None
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    if is_new:
        try:
            first_name = validate_required_string(data.get('first_name'), 'Ad')
            last_name = validate_required_string(data.get('last_name'), 'Soyad')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
        profile = VolunteerProfile(user_id=user.id, first_name=first_name, last_name=last_name)
        db.session.add(profile)
    else:
        if 'first_name' in data:
            try:
                profile.first_name = validate_required_string(data['first_name'], 'Ad')
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
        if 'last_name' in data:
            try:
                profile.last_name = validate_required_string(data['last_name'], 'Soyad')
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    optional_fields = ['phone', 'city', 'bio', 'interests', 'skills']
    for field in optional_fields:
        if field in data:
            try:
                setattr(profile, field, validate_optional_string(data[field], field))
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    if 'birth_date' in data and data['birth_date']:
        from datetime import date
        try:
            profile.birth_date = date.fromisoformat(data['birth_date'])
        except ValueError:
            return (jsonify({'error': 'birth_date YYYY-MM-DD formatında olmalıdır.'}), 400)
    db.session.commit()
    return (jsonify({'message': 'Profil oluşturuldu.' if is_new else 'Profil güncellendi.', 'volunteer': profile.to_dict()}), 201 if is_new else 200)

@volunteers_bp.route('/<int:volunteer_id>', methods=['GET'])
def get_volunteer(volunteer_id: int):
    profile = VolunteerProfile.query.get(volunteer_id)
    if not profile:
        return (jsonify({'error': 'Gönüllü bulunamadı.'}), 404)
    return (jsonify({'volunteer': profile.to_dict()}), 200)