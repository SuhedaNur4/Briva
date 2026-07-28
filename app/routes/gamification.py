from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.gamification import get_leaderboard, get_user_gamification, get_xp_history
from app.utils.auth_helpers import get_current_user, volunteer_required

gamification_bp = Blueprint('gamification', __name__)


@gamification_bp.route('/me', methods=['GET'])
@volunteer_required
def my_gamification():
    """Giriş yapan gönüllünün XP, seviye, ilerleme ve rozetleri.

    Tüm değerler backend'de gerçek veritabanı verisinden hesaplanır;
    frontend hiçbir hesap yapmaz (#38 madde 25).
    """
    user = get_current_user()
    return (jsonify(get_user_gamification(user.id)), 200)


@gamification_bp.route('/me/history', methods=['GET'])
@volunteer_required
def my_xp_history():
    """Giriş yapan gönüllünün sayfalanmış XP geçmişi. Başka kullanıcının geçmişi görülemez."""
    user = get_current_user()
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, max(1, int(request.args.get('per_page', 20))))
    except (TypeError, ValueError):
        return (jsonify({'error': 'page ve per_page tam sayı olmalıdır.'}), 400)
    return (jsonify(get_xp_history(user.id, page=page, per_page=per_page)), 200)


@gamification_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def leaderboard():
    """All-time XP liderlik tablosu (ilk 10) + mevcut kullanıcının sırası.

    Yalnızca public bilgiler döner: rank, user_id, görünen ad, xp (#38 madde 13).
    """
    user = get_current_user()
    current_user_id = user.id if user.role == 'volunteer' else None
    return (jsonify(get_leaderboard(limit=10, current_user_id=current_user_id)), 200)
