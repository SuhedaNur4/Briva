"""
quiz.py — Kişilik testi cevaplarını UserContext'e çevirir ve
/api/recommendations endpoint'ini proxy olarak kullanır.

POST /api/quiz/result
- Giriş yapılmamış kullanıcılar: Anlık öneri döndürür
- Giriş yapmış kullanıcılar (JWT opsiyonel): Ek olarak profil ilgi alanlarını günceller
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.extensions import db
from app.models.event import Event
from app.models.volunteer import VolunteerProfile
from app.recommend import RecommendationEngine, UserContext, RECOMMENDATION_THRESHOLD
from sqlalchemy.orm import selectinload

quiz_bp = Blueprint('quiz', __name__)

# Soru cevaplarını interest/skill kategorilerine eşle
ANSWER_INTEREST_MAP = {
    # Q1: Hafta sonu ne yaparsın?
    'q1_a': 'çevre', 'q1_b': 'eğitim', 'q1_c': 'sosyal destek', 'q1_d': 'hayvan hakları',
    # Q2: Hangi problem motive eder?
    'q2_a': 'çevre', 'q2_b': 'eğitim', 'q2_c': 'sosyal destek', 'q2_d': 'hayvan hakları',
    # Q3: Hangi projeye katılırsın?
    'q3_a': 'çevre', 'q3_b': 'eğitim', 'q3_c': 'sosyal destek', 'q3_d': 'hayvan hakları',
    # Q4: Gönüllülükte en değerli şey
    'q4_a': 'çevre', 'q4_b': 'eğitim', 'q4_c': 'sosyal destek', 'q4_d': 'hayvan hakları',
    # Q5: Hangisi heyecanlandırır?
    'q5_a': 'çevre', 'q5_b': 'eğitim', 'q5_c': 'sosyal destek', 'q5_d': 'hayvan hakları',
    # Q6: Hangi becerini kullanırsın?
    'q6_a': 'fiziksel destek', 'q6_b': 'eğitim', 'q6_c': 'sosyal destek', 'q6_d': 'hayvan hakları',
    # Q9: Uzun vadede ne yapmak istersin?
    'q9_a': 'çevre', 'q9_b': 'eğitim', 'q9_c': 'sosyal destek', 'q9_d': 'hayvan hakları',
    # Q10: Hangi haber etkiler?
    'q10_a': 'çevre', 'q10_b': 'eğitim', 'q10_c': 'sosyal destek', 'q10_d': 'hayvan hakları',
}

ANSWER_SKILL_MAP = {
    'q6_a': 'fiziksel destek',
    'q6_b': 'öğretme',
    'q6_c': 'empati ve dinleme',
    'q6_d': 'hayvan bakımı',
    'q14_a': 'kodlama',
    'q14_b': 'iletişim',
    'q14_c': 'müzik',
    'q14_d': 'öğretmenlik',
}

ANSWER_AVAILABILITY_MAP = {
    'q7_a': ['pazartesi', 'salı', 'çarşamba', 'perşembe', 'cuma'],
    'q7_b': ['cumartesi', 'pazar'],
    'q7_c': ['pazartesi', 'salı', 'çarşamba', 'perşembe', 'cuma', 'cumartesi', 'pazar'],
    'q7_d': ['cumartesi', 'pazar'],
}


def _extract_context(answers: dict) -> dict:
    """Quiz cevaplarından UserContext oluşturmak için gereken ham veriyi çıkar."""
    interests = []
    skills = []
    available_days = []
    city = answers.get('q11_city', '').strip()

    for key, value in answers.items():
        # Interest mapping
        mapped_interest = ANSWER_INTEREST_MAP.get(f'{key}_{value}')
        if mapped_interest and mapped_interest not in interests:
            interests.append(mapped_interest)

        # Skill mapping
        mapped_skill = ANSWER_SKILL_MAP.get(f'{key}_{value}')
        if mapped_skill and mapped_skill not in skills:
            skills.append(mapped_skill)

        # Availability mapping
        if key == 'q7':
            days = ANSWER_AVAILABILITY_MAP.get(f'q7_{value}', [])
            available_days = days

    return {
        'interests': interests,
        'skills': skills,
        'available_days': available_days,
        'city': city
    }


@quiz_bp.route('/result', methods=['POST'])
def quiz_result():
    """
    POST /api/quiz/result
    
    Body: { "answers": { "q1": "a", "q2": "b", ..., "q11_city": "istanbul" } }
    
    - Cevapları UserContext'e çevirir
    - Mevcut etkinliklerden öneri üretir
    - Giriş yapmış kullanıcılar için profil ilgi alanlarını günceller (isteğe bağlı)
    """
    data = request.get_json(silent=True)
    if not data or 'answers' not in data:
        return jsonify({'error': 'answers alanı zorunludur.'}), 400

    answers = data['answers']
    if not isinstance(answers, dict):
        return jsonify({'error': 'answers bir dict olmalıdır.'}), 400

    context_data = _extract_context(answers)

    # UserContext oluştur
    user_context = UserContext(
        city=context_data['city'],
        interests=context_data['interests'],
        skills=context_data['skills'],
        available_days=context_data['available_days']
    )

    # Öneri motoru çalıştır
    events = Event.query.options(
        selectinload(Event.organization)
    ).filter_by(status='published').all()

    engine = RecommendationEngine(threshold=0)  # Quiz için threshold düşük
    recommendations = engine.recommend(user_context, events)

    # Giriş yapmış kullanıcı için profil güncelle (opsiyonel)
    profile_updated = False
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        update_profile = data.get('update_profile', True)
        if user_id and update_profile and context_data['interests']:
            profile = VolunteerProfile.query.filter_by(user_id=int(user_id)).first()
            if profile:
                current_interests = profile.interests_list or []
                merged = list(set(current_interests + context_data['interests']))
                profile.interests = ','.join(merged)
                if context_data['skills']:
                    current_skills = profile.skills_list or []
                    merged_skills = list(set(current_skills + context_data['skills']))
                    profile.skills = ','.join(merged_skills)
                if context_data['city'] and not profile.city:
                    profile.city = context_data['city']
                db.session.commit()
                profile_updated = True
    except Exception:
        # JWT yoksa veya bir hata varsa sessizce geç
        pass

    return jsonify({
        'user_context': {
            'interests': context_data['interests'],
            'skills': context_data['skills'],
            'available_days': context_data['available_days'],
            'city': context_data['city'],
        },
        'profile_updated': profile_updated,
        'total_events_checked': len(events),
        'recommendations_count': len(recommendations),
        'recommendations': [r.to_dict() for r in recommendations[:6]]
    }), 200
