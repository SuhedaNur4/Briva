from app.utils.ai_analyzer import analyze_event_text
from tests.conftest import auth_header, register_and_login


def test_fallback_analysis_scores_detailed_listing_higher(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    poor = analyze_event_text(title='Etkinlik', description='Gelin.')
    rich = analyze_event_text(
        title='Sahil Temizliği Gönüllü Etkinliği',
        description=(
            'Kadıköy sahilinde birlikte temizlik yapacağız. Gönüllüler eldiven ve '
            'çöp poşetleriyle kıyı şeridini temizleyecek, toplanan atıklar geri '
            'dönüşüme gönderilecek. Topluluk olarak çevreye somut bir katkı '
            'sağlamak isteyen herkesi bekliyoruz. Etkinlik sonunda kısa bir '
            'değerlendirme ve teşekkür buluşması yapılacaktır.'
        ),
        category='cevre',
        city='Istanbul',
        requirements='Fiziksel aktiviteye uygunluk',
    )
    assert rich['quality_score'] > poor['quality_score']
    assert rich['source'] == 'fallback'
    assert 0 <= poor['quality_score'] <= 100


def test_fallback_flags_missing_fields(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    result = analyze_event_text(title='Kısa', description='')
    assert result['weaknesses']
    assert result['suggestions']


def test_analyze_endpoint_requires_jwt(client):
    assert client.post('/api/ai/analyze-event', json={'title': 'x'}).status_code == 401


def test_analyze_endpoint_with_draft_text(client, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    token = register_and_login(client, 'analiz@briva.com', role='organization')
    response = client.post(
        '/api/ai/analyze-event',
        json={'title': 'Kitap Bağış Kampanyası', 'description': 'Köy okullarına kitap topluyoruz.'},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    analysis = response.get_json()['analysis']
    assert 'quality_score' in analysis
    assert analysis['source'] in ('gemini', 'fallback')


def test_analyze_endpoint_missing_input_returns_400(client):
    token = register_and_login(client, 'analiz2@briva.com')
    response = client.post('/api/ai/analyze-event', json={}, headers=auth_header(token))
    assert response.status_code == 400


def test_analyze_endpoint_unknown_event_returns_404(client):
    token = register_and_login(client, 'analiz3@briva.com')
    response = client.post(
        '/api/ai/analyze-event', json={'event_id': 12345}, headers=auth_header(token)
    )
    assert response.status_code == 404
