from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.models.event import Event
from app.utils.ai_analyzer import analyze_event_text
from app.utils.validators import parse_request_json

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/analyze-event', methods=['POST'])
@jwt_required()
def analyze_event():
    """Etkinlik ilanının kalitesini AI ile analiz eder.

    İki kullanım şekli:
    1. {"event_id": 5} → mevcut bir etkinliği analiz eder.
    2. {"title": "...", "description": "..."} → henüz kaydedilmemiş
       taslak bir ilanı analiz eder (STK, ilanı yayınlamadan önce test edebilir).
    """
    try:
        data = parse_request_json(request)
    except ValueError as e:
        return (jsonify({'error': str(e)}), 400)

    event_id = data.get('event_id')
    if event_id is not None:
        event = Event.query.get(event_id)
        if not event:
            return (jsonify({'error': 'Etkinlik bulunamadı.'}), 404)
        title = event.title
        description = event.description or ''
        category = event.category or ''
        city = event.city or ''
        requirements = event.requirements or ''
    else:
        title = str(data.get('title') or '').strip()
        description = str(data.get('description') or '').strip()
        category = str(data.get('category') or '').strip()
        city = str(data.get('city') or '').strip()
        requirements = str(data.get('requirements') or '').strip()
        if not title and not description:
            return (
                jsonify({'error': "'event_id' veya en azından 'title'/'description' gereklidir."}),
                400,
            )

    analysis = analyze_event_text(
        title=title,
        description=description,
        category=category,
        city=city,
        requirements=requirements,
    )
    return (jsonify({'analysis': analysis}), 200)
