from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.application import EventApplication
from app.models.event import Event
from app.models.feedback import FEEDBACK_DISLIKE, FEEDBACK_LIKE, RecommendationFeedback
from app.models.user import User
from app.recommend import RecommendationEngine, UserContext, RECOMMENDATION_THRESHOLD
from app.utils.auth_helpers import get_current_user, volunteer_required, organization_required
from app.utils.validators import parse_request_json
from app.utils.ai_analyzer import evaluate_applicant_with_gemini, explain_recommendation_with_gemini
import os
import json

recommendations_bp = Blueprint('recommendations', __name__)

def _feedback_signals_for(user_id: int) -> tuple[list[str], list[str], set, set]:
    """Kullanıcının geçmiş geri bildirimlerinden öneri motoru sinyalleri türetir (issue #19)."""
    feedbacks = (
        RecommendationFeedback.query.filter_by(user_id=user_id)
        .join(Event, RecommendationFeedback.event_id == Event.id)
        .add_columns(Event.category)
        .all()
    )
    liked_categories, disliked_categories = [], []
    liked_event_ids, disliked_event_ids = set(), set()
    for feedback, category in feedbacks:
        if feedback.status == FEEDBACK_LIKE:
            liked_event_ids.add(feedback.event_id)
            if category:
                liked_categories.append(category)
        elif feedback.status == FEEDBACK_DISLIKE:
            disliked_event_ids.add(feedback.event_id)
            if category:
                disliked_categories.append(category)
    return liked_categories, disliked_categories, liked_event_ids, disliked_event_ids


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
    
    # Geçmiş başvuruları ve katılımları ekle
    applications = EventApplication.query.filter_by(user_id=user.id).all()
    past_apps = []
    past_parts = []
    for app in applications:
        if app.event and app.event.title:
            if app.status == 'completed':
                past_parts.append(app.event.title)
            else:
                past_apps.append(app.event.title)
    
    user_context.past_applications = past_apps
    user_context.past_participations = past_parts
    
    liked_cats, disliked_cats, liked_ids, disliked_ids = _feedback_signals_for(user.id)
    user_context.with_feedback(liked_cats, disliked_cats, liked_ids, disliked_ids)
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
    
    context_text = user_context.get_context_text().strip()
    is_empty_profile = not context_text
    
    explanation_text = ""
    is_ai_generated = False
    if is_empty_profile:
        explanation_text = "Profilindeki bilgiler bu etkinlik için yeterli kişiselleştirme sağlamıyor. Sana özel öneriler için 15 soruluk testi tamamlayabilirsin."
    else:
        # Gemini ile açıklama üret (Kişiselleştirilmiş AI Explanation)
        event_context = f"Başlık: {event.title} | Açıklama: {event.description} | Kategori: {event.category} | Gereksinimler: {event.requirements}"
        result = explain_recommendation_with_gemini(context_text, event_context)
        explanation_text = result.get('explanation', '')
        is_ai_generated = result.get('ai_generated', False)
                
    rec_engine = RecommendationEngine()
    scored = rec_engine.score_event(user_context, event)
    
    if not explanation_text:
        # Fallback (Rule-based)
        explanation_text = "Bu etkinlik genel profil kriterlerinize temel düzeyde uyum sağlamaktadır."
        is_ai_generated = False
        
    return (jsonify({
        'explanation': {
            'text': explanation_text,
            'is_empty_profile': is_empty_profile,
            'ai_generated': is_ai_generated,
            'fallback_used': not is_ai_generated,
            'total_score': scored.total_score,
            'matching_details': scored.matching_details
        }
    }), 200)

@recommendations_bp.route('/evaluate-applicant', methods=['POST'])
@jwt_required()
@organization_required
def evaluate_applicant():
    user = get_current_user()
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)
    app_id = data.get('application_id')
    event_id = data.get('event_id')
    applicant_id = data.get('user_id') or data.get('applicant_id')
    application = None
    if app_id:
        application = EventApplication.query.get(int(app_id))
        if not application:
            return (jsonify({'error': 'Başvuru bulunamadı.'}), 404)
        event = application.event
        applicant = application.user
    elif event_id and applicant_id:
        event = Event.query.get(int(event_id))
        if not event:
            return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
        applicant = User.query.get(int(applicant_id))
        if not applicant:
            return (jsonify({'error': 'Aday bulunamadı.'}), 404)
        application = EventApplication.query.filter_by(event_id=event.id, user_id=applicant.id).first()
    else:
        return (jsonify({'error': 'application_id veya (event_id ve user_id) parametreleri zorunludur.'}), 400)
    if not user.organization or event.organization_id != user.organization.id:
        return (jsonify({'error': 'Bu adayı değerlendirme yetkiniz yok.'}), 403)
    vp = applicant.volunteer_profile
    if not vp:
        return (jsonify({'error': 'Adayın profil detayları bulunamadı.'}), 400)
    req_list = [r.strip().lower() for r in (event.requirements or '').split(',') if r.strip()]
    cand_skills_lower = [s.lower() for s in vp.skills_list]
    matching_skills = [s for s in vp.skills_list if s.lower() in req_list]
    cand_interests_lower = [i.lower() for i in vp.interests_list]
    event_cat = (event.category or '').strip()
    matching_interests = [event_cat] if event_cat and event_cat.lower() in cand_interests_lower else []
    city_matched = bool(event.city and vp.city and event.city.strip().lower() == vp.city.strip().lower())
    reasons = []
    if matching_skills:
        reasons.append(f"{', '.join(matching_skills)} becerisi etkinlik gereksinimleriyle örtüşüyor.")
    if matching_interests:
        reasons.append(f"'{event_cat}' alanı adayın ilgi alanlarıyla örtüşüyor.")
    if city_matched:
        reasons.append(f"{vp.city}'da bulunuyor (Etkinlik konumuyla uyumlu).")
    elif vp.city:
        reasons.append(f"Aday {vp.city}'da bulunuyor (Etkinlik konumu: {event.city or 'Belirtilmedi'}).")
    missing_info = []
    if not vp.skills_list:
        missing_info.append("Aday profilinde henüz beceri listesi belirtilmemiş.")
    if not vp.interests_list:
        missing_info.append("Aday profilinde henüz ilgi alanları belirtilmemiş.")
    if not vp.city:
        missing_info.append("Aday profilinde şehir bilgisi bulunmuyor.")
    if not req_list:
        missing_info.append("Etkinlik için özel beceri kriteri tanımlanmamış.")
    summary = "Bu aday etkinliğiniz için uygun olabilir." if (matching_skills or matching_interests or city_matched) else "Adayın profil bilgileri ile etkinlik kriterleri arasında doğrudan eşleşme tespit edilemedi."

    # Gemini ile Semantik Değerlendirme
    applicant_data = {
        'bio': vp.bio,
        'interests': vp.interests_list,
        'skills': vp.skills_list,
        'city': vp.city
    }
    event_data = {
        'title': event.title,
        'description': event.description,
        'requirements': event.requirements,
        'category': event.category,
        'city': event.city
    }
    
    evaluation_result = evaluate_applicant_with_gemini(applicant_data, event_data)
    
    # Eğer Gemini hata verirse veya anahtar yoksa evaluate_applicant_with_gemini fallback döner.
    # Yine de None gelirse (eski sistem) manuel fallback yap.
    if not evaluation_result:
        evaluation_result = {
            'match_score': 80 if (matching_skills and city_matched) else (60 if matching_skills or matching_interests else 40),
            'summary': summary,
            'strengths': matching_skills + (matching_interests if matching_interests else []),
            'gaps': missing_info,
            'recommendation': 'strong_match' if matching_skills and city_matched else ('possible_match' if matching_skills or matching_interests else 'weak_match'),
            'source': 'rule-based',
            'ai_generated': False,
            'fallback_used': True
        }

    return (jsonify({
        'applicant': {
            'user_id': vp.user_id,
            'full_name': vp.full_name,
            'city': vp.city,
            'skills': vp.skills_list,
            'interests': vp.interests_list,
            'bio': vp.bio
        },
        'event': {
            'id': event.id,
            'title': event.title,
            'category': event.category,
            'city': event.city,
            'requirements': event.requirements
        },
        'evaluation': evaluation_result,
        'rule_based_details': {
            'matching_skills': matching_skills,
            'matching_interests': matching_interests,
            'city_match': city_matched,
            'reasons': reasons,
            'missing_info': missing_info
        }
    }), 200)