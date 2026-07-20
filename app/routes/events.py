from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from app.extensions import db
from app.models.event import Event
from app.models.application import EventApplication
from app.utils.auth_helpers import get_current_user, organization_required, volunteer_required
from app.utils.validators import parse_request_json, validate_required_string, validate_optional_string, validate_positive_int, validate_event_status
from app.utils.ai_analyzer import analyze_event_text, compact_analysis
from app.routes.notifications import create_notification
events_bp = Blueprint('events', __name__)

def _parse_datetime(value: str, field_name: str) -> datetime:
    if not value:
        raise ValueError(f'{field_name} zorunludur.')
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f'{field_name} ISO 8601 formatında olmalıdır. Örnek: 2025-08-15T09:00:00')

@events_bp.route('', methods=['POST'])
@jwt_required()
@organization_required
def create_event():
    user = get_current_user()
    if not user.organization:
        return (jsonify({'error': 'Etkinlik oluşturmak için önce STK profilinizi oluşturun.'}), 400)
    try:
        data = parse_request_json(request)
        title = validate_required_string(data.get('title'), 'Etkinlik başlığı')
        start_date = _parse_datetime(data.get('start_date'), 'Başlangıç tarihi')
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    event = Event(organization_id=user.organization.id, title=title, start_date=start_date)
    for field in ['description', 'category', 'city', 'address', 'requirements']:
        if field in data:
            try:
                setattr(event, field, validate_optional_string(data[field], field))
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    if data.get('end_date'):
        try:
            event.end_date = _parse_datetime(data['end_date'], 'Bitiş tarihi')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    if data.get('max_volunteers') is not None:
        try:
            event.max_volunteers = validate_positive_int(data['max_volunteers'], 'Maksimum gönüllü')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    db.session.add(event)
    db.session.commit()
    # Issue #18: etkinlik oluşturulurken açıklama kalitesi AI ile analiz edilip yanıtla döner
    analysis = analyze_event_text(
        title=event.title,
        description=event.description or '',
        category=event.category or '',
        city=event.city or '',
        requirements=event.requirements or '',
    )
    return (jsonify({'message': 'Etkinlik oluşturuldu.', 'event': event.to_dict(), 'ai_analysis': compact_analysis(analysis)}), 201)

@events_bp.route('', methods=['GET'])
def list_events():
    query = Event.query
    keyword = request.args.get('q')
    if keyword:
        pattern = f'%{keyword.strip()}%'
        query = query.filter(
            db.or_(
                Event.title.ilike(pattern),
                Event.description.ilike(pattern),
                Event.requirements.ilike(pattern),
            )
        )
    start_after = request.args.get('start_after')
    if start_after:
        try:
            query = query.filter(Event.start_date >= _parse_datetime(start_after, 'start_after'))
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    start_before = request.args.get('start_before')
    if start_before:
        try:
            query = query.filter(Event.start_date <= _parse_datetime(start_before, 'start_before'))
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    city = request.args.get('city')
    if city:
        query = query.filter(Event.city.ilike(f'%{city}%'))
    category = request.args.get('category')
    if category:
        query = query.filter(Event.category.ilike(f'%{category}%'))
    status = request.args.get('status', 'published')
    query = query.filter(Event.status == status)
    org_id = request.args.get('organization_id')
    if org_id:
        try:
            query = query.filter(Event.organization_id == int(org_id))
        except ValueError:
            pass
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except ValueError:
        page, per_page = (1, 20)
    pagination = query.order_by(Event.start_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return (jsonify({'events': [e.to_dict() for e in pagination.items], 'pagination': {'page': pagination.page, 'per_page': pagination.per_page, 'total': pagination.total, 'pages': pagination.pages}}), 200)

@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id: int):
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    user_application_status = None
    try:
        verify_jwt_in_request(optional=True)
        user = get_current_user()
        if user and user.role == 'volunteer':
            app_record = EventApplication.query.filter_by(user_id=user.id, event_id=event_id).first()
            if app_record:
                user_application_status = app_record.status
    except Exception:
        pass
    data = event.to_dict()
    data['my_application_status'] = user_application_status
    return (jsonify({'event': data}), 200)

@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
@organization_required
def update_event(event_id: int):
    user = get_current_user()
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    if not user.organization or event.organization_id != user.organization.id:
        return (jsonify({'error': 'Bu etkinliği güncelleme yetkiniz yok.'}), 403)
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    if 'title' in data:
        try:
            event.title = validate_required_string(data['title'], 'Etkinlik başlığı')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    for field in ['description', 'category', 'city', 'address', 'requirements']:
        if field in data:
            try:
                setattr(event, field, validate_optional_string(data[field], field))
            except ValueError as e:
                return (jsonify({'error': str(e)}), 400)
    if 'start_date' in data:
        try:
            event.start_date = _parse_datetime(data['start_date'], 'Başlangıç tarihi')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    if 'end_date' in data:
        try:
            event.end_date = _parse_datetime(data['end_date'], 'Bitiş tarihi') if data['end_date'] else None
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    if 'max_volunteers' in data:
        try:
            event.max_volunteers = validate_positive_int(data['max_volunteers'], 'Maksimum gönüllü')
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    if 'status' in data:
        try:
            event.status = validate_event_status(data['status'])
        except ValueError as e:
            return (jsonify({'error': str(e)}), 400)
    db.session.commit()
    return (jsonify({'message': 'Etkinlik güncellendi.', 'event': event.to_dict()}), 200)

@events_bp.route('/<int:event_id>/apply', methods=['POST'])
@jwt_required()
@volunteer_required
def apply_to_event(event_id: int):
    user = get_current_user()
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    if event.status != 'published':
        return (jsonify({'error': 'Bu etkinliğe başvuru kabul edilmiyor.'}), 400)
    if event.is_full:
        return (jsonify({'error': 'Etkinlik kapasitesi dolmuştur.'}), 400)
    existing = EventApplication.query.filter_by(user_id=user.id, event_id=event_id).first()
    if existing:
        return (jsonify({'error': 'Bu etkinliğe zaten başvurdunuz.', 'application': existing.to_dict()}), 409)
    data = request.get_json(silent=True) or {}
    cover_letter = data.get('cover_letter', '')
    if cover_letter and len(cover_letter) > 2000:
        return (jsonify({'error': 'Başvuru notu en fazla 2000 karakter olabilir.'}), 400)
    application = EventApplication(user_id=user.id, event_id=event_id, cover_letter=cover_letter or None)
    db.session.add(application)
    db.session.commit()
    
    # STK Yetkilisine Bildirim Gönder (Yeni Gönüllü Başvurusu)
    if event.organization and event.organization.user_id:
        volunteer_name = getattr(user, 'volunteer_profile', None) and user.volunteer_profile.full_name or user.email
        create_notification(
            user_id=event.organization.user_id,
            message=f"'{event.title}' etkinliğine '{volunteer_name}' yeni bir başvuru yaptı.",
            notif_type='new_application',
            related_event_id=event.id
        )
        db.session.commit()

    return (jsonify({'message': 'Başvurunuz alındı.', 'application': application.to_dict(include_event=True)}), 201)

@events_bp.route('/<int:event_id>/applications', methods=['GET'])
@jwt_required()
@organization_required
def get_event_applications(event_id: int):
    user = get_current_user()
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    if not user.organization or event.organization_id != user.organization.id:
        return (jsonify({'error': 'Bu etkinliğin başvurularını görme yetkiniz yok.'}), 403)
    query = EventApplication.query.filter_by(event_id=event_id)
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(EventApplication.status == status_filter)
    applications = query.order_by(EventApplication.applied_at.asc()).all()
    return (jsonify({'event_id': event_id, 'event_title': event.title, 'applications': [a.to_dict(include_user=True) for a in applications], 'total': len(applications)}), 200)