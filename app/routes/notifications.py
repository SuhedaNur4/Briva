from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.notification import Notification
from app.utils.auth_helpers import get_current_user

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    """Giriş yapan kullanıcının bildirimlerini listeler (?unread=true ile filtrelenebilir)."""
    user = get_current_user()
    query = Notification.query.filter_by(user_id=user.id)
    if request.args.get('unread', '').lower() == 'true':
        query = query.filter(Notification.is_read.is_(False))
    notifications = query.order_by(Notification.created_at.desc()).limit(100).all()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return (
        jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'total': len(notifications),
            'unread_count': unread_count,
        }),
        200,
    )


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id: int):
    """Tek bir bildirimi okundu olarak işaretler."""
    user = get_current_user()
    notification = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if not notification:
        return (jsonify({'error': 'Bildirim bulunamadı.'}), 404)
    notification.is_read = True
    db.session.commit()
    return (jsonify({'message': 'Bildirim okundu olarak işaretlendi.', 'notification': notification.to_dict()}), 200)


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """Tüm bildirimleri okundu olarak işaretler."""
    user = get_current_user()
    updated = Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return (jsonify({'message': f'{updated} bildirim okundu olarak işaretlendi.'}), 200)


def create_notification(user_id: int, message: str, notif_type: str = 'general', related_event_id: int | None = None) -> Notification:
    """Diğer servislerin bildirim üretmesi için yardımcı fonksiyon (commit çağıranın sorumluluğunda)."""
    notification = Notification(
        user_id=user_id,
        message=message,
        notif_type=notif_type,
        related_event_id=related_event_id,
    )
    db.session.add(notification)
    return notification
