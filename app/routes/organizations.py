from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.organization import Organization
from app.utils.auth_helpers import get_current_user, organization_required
from app.utils.validators import parse_request_json, validate_required_string, validate_optional_string
organizations_bp = Blueprint('organizations', __name__)

@organizations_bp.route('', methods=['POST'])
@jwt_required()
@organization_required
def create_organization():
    user = get_current_user()
    if user.organization:
        return (jsonify({'error': 'STK profiliniz zaten mevcut. PUT ile güncelleyebilirsiniz.'}), 409)
    try:
        data = parse_request_json(request)
        name = validate_required_string(data.get('name'), 'Kuruluş adı')
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    org = Organization(user_id=user.id, name=name)
    optional_fields = ['description', 'website', 'phone', 'address', 'city']
    for field in optional_fields:
        if field in data:
            try:
                setattr(org, field, validate_optional_string(data[field], field))
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    db.session.add(org)
    db.session.commit()
    return (jsonify({'message': 'STK profili oluşturuldu.', 'organization': org.to_dict()}), 201)

@organizations_bp.route('', methods=['GET'])
def list_organizations():
    query = Organization.query
    city = request.args.get('city')
    if city:
        query = query.filter(Organization.city.ilike(f'%{city}%'))
    verified = request.args.get('verified')
    if verified is not None:
        query = query.filter(Organization.is_verified == (verified.lower() == 'true'))
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except ValueError:
        page, per_page = (1, 20)
    pagination = query.order_by(Organization.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return (jsonify({'organizations': [org.to_dict() for org in pagination.items], 'pagination': {'page': pagination.page, 'per_page': pagination.per_page, 'total': pagination.total, 'pages': pagination.pages}}), 200)

@organizations_bp.route('/<int:org_id>', methods=['GET'])
def get_organization(org_id: int):
    org = Organization.query.get(org_id)
    if not org:
        return (jsonify({'error': 'STK bulunamadı.'}), 404)
    return (jsonify({'organization': org.to_dict(include_events=True)}), 200)

@organizations_bp.route('/<int:org_id>', methods=['PUT'])
@jwt_required()
@organization_required
def update_organization(org_id: int):
    user = get_current_user()
    org = Organization.query.get(org_id)
    if not org:
        return (jsonify({'error': 'STK bulunamadı.'}), 404)
    if org.user_id != user.id:
        return (jsonify({'error': 'Bu STK profilini güncelleme yetkiniz yok.'}), 403)
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    if 'name' in data:
        try:
            org.name = validate_required_string(data['name'], 'Kuruluş adı')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    optional_fields = ['description', 'website', 'phone', 'address', 'city']
    for field in optional_fields:
        if field in data:
            try:
                setattr(org, field, validate_optional_string(data[field], field))
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    db.session.commit()
    return (jsonify({'message': 'STK profili güncellendi.', 'organization': org.to_dict()}), 200)