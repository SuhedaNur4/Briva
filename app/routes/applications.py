from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.application import EventApplication
from app.utils.auth_helpers import get_current_user
from app.utils.validators import parse_request_json, validate_application_status, validate_optional_string
applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/my', methods=['GET'])
@jwt_required()
def my_applications():
    user = get_current_user()
    query = EventApplication.query.filter_by(user_id=user.id)
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(EventApplication.status == status_filter)
    applications = query.order_by(EventApplication.applied_at.desc()).all()
    return (jsonify({'applications': [a.to_dict(include_event=True) for a in applications], 'total': len(applications)}), 200)

@applications_bp.route('/<int:application_id>', methods=['PUT'])
@jwt_required()
def update_application(application_id: int):
    user = get_current_user()
    application = EventApplication.query.get(application_id)
    if not application:
        return (jsonify({'error': 'Başvuru bulunamadı.'}), 404)
    try:
        data = parse_request_json(request)
        new_status = validate_application_status(data.get('status'))
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    is_owner = application.user_id == user.id
    is_org_owner = user.role == 'organization' and user.organization is not None and (application.event.organization_id == user.organization.id)
    if not is_owner and (not is_org_owner):
        return (jsonify({'error': 'Bu başvuruyu güncelleme yetkiniz yok.'}), 403)
    if is_owner:
        if new_status != 'cancelled':
            return (jsonify({'error': 'Gönüllüler başvurularını yalnızca iptal edebilir.'}), 400)
        if application.status in ('approved', 'rejected'):
            return (jsonify({'error': 'Onaylanan veya reddedilen başvuru iptal edilemez.'}), 400)
    if is_org_owner:
        if new_status == 'cancelled':
            return (jsonify({'error': 'STK kullanıcıları başvuruyu iptal edemez.'}), 400)
        if application.status == 'cancelled':
            return (jsonify({'error': 'İptal edilmiş başvuru işleme alınamaz.'}), 400)
        if new_status == 'approved' and application.event.is_full:
            return (jsonify({'error': 'Etkinlik kapasitesi dolmuştur.'}), 400)
        if 'reviewer_note' in data:
            try:
                application.reviewer_note = validate_optional_string(data['reviewer_note'], 'İnceleyici notu', max_length=1000)
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    application.status = new_status
    db.session.commit()
    return (jsonify({'message': f"Başvuru durumu '{new_status}' olarak güncellendi.", 'application': application.to_dict(include_event=True, include_user=is_org_owner)}), 200)