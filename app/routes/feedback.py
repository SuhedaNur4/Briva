from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.event import Event
from app.models.feedback import VALID_FEEDBACK_VALUES, RecommendationFeedback
from app.utils.auth_helpers import get_current_user, volunteer_required
from app.utils.validators import parse_request_json

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/my', methods=['GET'])
@jwt_required()
def my_feedbacks():
    """Giriş yapan kullanıcının verdiği geri bildirimleri listeler."""
    user = get_current_user()
    feedbacks = (
        RecommendationFeedback.query.filter_by(user_id=user.id)
        .order_by(RecommendationFeedback.updated_at.desc())
        .all()
    )
    return (
        jsonify({'feedbacks': [f.to_dict(include_event=True) for f in feedbacks], 'total': len(feedbacks)}),
        200,
    )


@feedback_bp.route('/<int:event_id>', methods=['POST'])
@volunteer_required
def give_feedback(event_id: int):
    """Bir etkinlik önerisine 'like' veya 'dislike' geri bildirimi verir.

    Aynı etkinliğe tekrar geri bildirim verilirse mevcut kayıt güncellenir (upsert).
    """
    user = get_current_user()
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    feedback_value = str(data.get('feedback') or '').strip().lower()
    if feedback_value not in VALID_FEEDBACK_VALUES:
        return (
            jsonify({'error': f"Geçersiz geri bildirim. Geçerli değerler: {', '.join(VALID_FEEDBACK_VALUES)}"}),
            400,
        )
    record = RecommendationFeedback.query.filter_by(user_id=user.id, event_id=event_id).first()
    if record:
        record.status = feedback_value
        status_code = 200
        message = 'Geri bildirim güncellendi.'
    else:
        record = RecommendationFeedback(user_id=user.id, event_id=event_id, status=feedback_value)
        db.session.add(record)
        status_code = 201
        message = 'Geri bildirim kaydedildi.'
    db.session.commit()
    return (jsonify({'message': message, 'feedback': record.to_dict()}), status_code)


@feedback_bp.route('/<int:event_id>', methods=['DELETE'])
@volunteer_required
def remove_feedback(event_id: int):
    """Bir etkinliğe verilen geri bildirimi kaldırır."""
    user = get_current_user()
    record = RecommendationFeedback.query.filter_by(user_id=user.id, event_id=event_id).first()
    if not record:
        return (jsonify({'error': 'Bu etkinlik için geri bildiriminiz yok.'}), 404)
    db.session.delete(record)
    db.session.commit()
    return (jsonify({'message': 'Geri bildirim kaldırıldı.'}), 200)
