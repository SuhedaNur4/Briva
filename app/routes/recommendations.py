from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.event import Event
from app.recommend import RecommendationEngine, UserContext, RECOMMENDATION_THRESHOLD
from app.utils.auth_helpers import get_current_user, volunteer_required
from app.utils.validators import parse_request_json
recommendations_bp = Blueprint('recommendations', __name__)

def _get_all_active_events() -> list:
    return Event.query.options(selectinload(Event.organization), selectinload(Event.applications)).filter_by(status='published').all()

@recommendations_bp.route('', methods=['POST'])
def recommend():
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    user_context = UserContext.from_dict(data)
    threshold = data.get('threshold', RECOMMENDATION_THRESHOLD)
    if not isinstance(threshold, int) or threshold < 0 or threshold > 200:
        threshold = RECOMMENDATION_THRESHOLD
    rec_engine = RecommendationEngine(threshold=threshold)
    events = _get_all_active_events()
    recommendations = rec_engine.recommend(user_context, events)
    return (jsonify({'user_context': {'city': user_context.city, 'interests': user_context.interests, 'skills': user_context.skills, 'available_days': user_context.available_days}, 'threshold': threshold, 'total_events_checked': len(events), 'recommendations_count': len(recommendations), 'recommendations': [r.to_dict() for r in recommendations]}), 200)

@recommendations_bp.route('/me', methods=['GET'])
@jwt_required()
@volunteer_required
def recommend_for_me():
    user = get_current_user()
    if not user.volunteer_profile:
        return (jsonify({'error': 'Öneri alabilmek için önce gönüllü profilinizi oluşturun.', 'hint': 'PUT /api/volunteers/me ile profilinizi oluşturun.'}), 400)
    user_context = UserContext.from_volunteer_profile(user.volunteer_profile)
    try:
        threshold = int(request.args.get('threshold', RECOMMENDATION_THRESHOLD))
        if threshold < 0 or threshold > 200:
            threshold = RECOMMENDATION_THRESHOLD
    except (ValueError, TypeError):
        threshold = RECOMMENDATION_THRESHOLD
    rec_engine = RecommendationEngine(threshold=threshold)
    events = _get_all_active_events()
    recommendations = rec_engine.recommend(user_context, events)
    return (jsonify({'volunteer': {'user_id': user.id, 'full_name': user.volunteer_profile.full_name}, 'user_context': {'city': user_context.city, 'interests': user_context.interests, 'skills': user_context.skills, 'available_days': user_context.available_days}, 'threshold': threshold, 'total_events_checked': len(events), 'recommendations_count': len(recommendations), 'recommendations': [r.to_dict() for r in recommendations]}), 200)

@recommendations_bp.route('/explain', methods=['POST'])
def explain():
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    event_id = data.get('event_id')
    if not event_id:
        return (jsonify({'error': 'event_id zorunludur.'}), 400)
    event = Event.query.get(int(event_id))
    if not event:
        return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
    user_context = UserContext.from_dict(data)
    rec_engine = RecommendationEngine()
    explanation = rec_engine.explain(user_context, event)
    return (jsonify({'explanation': explanation}), 200)