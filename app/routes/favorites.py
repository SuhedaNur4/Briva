from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.event import Event
from app.models.favorite import Favorite
from app.utils.auth_helpers import get_current_user, volunteer_required

favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('', methods=['GET'])
@jwt_required()
def list_favorites():
    """Giriş yapan kullanıcının favori etkinliklerini listeler."""
    user = get_current_user()
    favorites = (
        Favorite.query.filter_by(user_id=user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return (
        jsonify({'favorites': [f.to_dict() for f in favorites], 'total': len(favorites)}),
        200,
    )


@favorites_bp.route('/<int:event_id>', methods=['POST'])
@volunteer_required
def add_favorite(event_id: int):
    """Bir etkinliği favorilere ekler (yalnızca gönüllüler)."""
    user = get_current_user()
    event = Event.query.get(event_id)
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    existing = Favorite.query.filter_by(user_id=user.id, event_id=event_id).first()
    if existing:
        return (jsonify({'error': 'Bu etkinlik zaten favorilerinizde.'}), 409)
    favorite = Favorite(user_id=user.id, event_id=event_id)
    db.session.add(favorite)
    db.session.commit()
    return (
        jsonify({'message': 'Etkinlik favorilere eklendi.', 'favorite': favorite.to_dict()}),
        201,
    )


@favorites_bp.route('/<int:event_id>', methods=['DELETE'])
@volunteer_required
def remove_favorite(event_id: int):
    """Bir etkinliği favorilerden çıkarır."""
    user = get_current_user()
    favorite = Favorite.query.filter_by(user_id=user.id, event_id=event_id).first()
    if not favorite:
        return (jsonify({'error': 'Bu etkinlik favorilerinizde değil.'}), 404)
    db.session.delete(favorite)
    db.session.commit()
    return (jsonify({'message': 'Etkinlik favorilerden çıkarıldı.'}), 200)
