from tests.conftest import auth_header, register_and_login


def _setup_org(client, email='stk-s2@briva.com'):
    token = register_and_login(client, email, role='organization')
    client.post('/api/organizations', json={'name': 'Sprint2 STK', 'city': 'Istanbul'}, headers=auth_header(token))
    return token


def _create_event(client, org_token, title, category='cevre', description='', start='2026-08-15T09:00:00'):
    response = client.post(
        '/api/events',
        json={'title': title, 'start_date': start, 'city': 'Istanbul', 'category': category, 'description': description},
        headers=auth_header(org_token),
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()['event']['id']


# ---------------- #12 / #21: Gelişmiş arama ----------------

def test_search_by_keyword(client):
    org = _setup_org(client)
    _create_event(client, org, 'Sahil Temizliği', description='Kadıköy sahilinde çöp toplama')
    _create_event(client, org, 'Kitap Bağışı', category='egitim', description='Köy okullarına kitap')

    response = client.get('/api/events?q=sahil')
    body = response.get_json()
    assert response.status_code == 200
    assert body['pagination']['total'] == 1
    assert 'Sahil' in body['events'][0]['title']


def test_search_by_date_range(client):
    org = _setup_org(client)
    _create_event(client, org, 'Temmuz Etkinliği', start='2026-07-20T10:00:00')
    _create_event(client, org, 'Eylül Etkinliği', start='2026-09-20T10:00:00')

    response = client.get('/api/events?start_after=2026-08-01T00:00:00')
    body = response.get_json()
    assert body['pagination']['total'] == 1
    assert body['events'][0]['title'] == 'Eylül Etkinliği'

    response = client.get('/api/events?start_before=2026-08-01T00:00:00')
    assert response.get_json()['events'][0]['title'] == 'Temmuz Etkinliği'


def test_search_invalid_date_returns_400(client):
    assert client.get('/api/events?start_after=gecersiz').status_code == 400


# ---------------- #14: Geri bildirim ----------------

def test_feedback_upsert_flow(client):
    org = _setup_org(client)
    event_id = _create_event(client, org, 'Fidan Dikimi')
    token = register_and_login(client, 'fb1@briva.com')

    first = client.post(f'/api/feedback/{event_id}', json={'feedback': 'like'}, headers=auth_header(token))
    assert first.status_code == 201

    second = client.post(f'/api/feedback/{event_id}', json={'feedback': 'dislike'}, headers=auth_header(token))
    assert second.status_code == 200
    assert second.get_json()['feedback']['status'] == 'dislike'

    listing = client.get('/api/feedback/my', headers=auth_header(token))
    assert listing.get_json()['total'] == 1


def test_feedback_invalid_value_returns_400(client):
    org = _setup_org(client)
    event_id = _create_event(client, org, 'Test Etkinliği')
    token = register_and_login(client, 'fb2@briva.com')
    response = client.post(f'/api/feedback/{event_id}', json={'feedback': 'harika'}, headers=auth_header(token))
    assert response.status_code == 400


def test_feedback_delete(client):
    org = _setup_org(client)
    event_id = _create_event(client, org, 'Silinecek Feedback')
    token = register_and_login(client, 'fb3@briva.com')
    client.post(f'/api/feedback/{event_id}', json={'feedback': 'like'}, headers=auth_header(token))
    assert client.delete(f'/api/feedback/{event_id}', headers=auth_header(token)).status_code == 200
    assert client.delete(f'/api/feedback/{event_id}', headers=auth_header(token)).status_code == 404


# ---------------- #19: Feedback → Öneri motoru ----------------

def test_feedback_changes_recommendation_score(client):
    from app.recommend import UserContext, RecommendationEngine
    from app.models.event import Event

    org = _setup_org(client)
    event_id = _create_event(client, org, 'Orman Temizliği', category='cevre')
    event = Event.query.get(event_id)
    engine = RecommendationEngine()

    base_ctx = UserContext(city='istanbul', interests=['cevre'])
    base_score = engine.score_event(base_ctx, event).total_score

    liked_ctx = UserContext(city='istanbul', interests=['cevre'], liked_categories=['cevre'])
    disliked_ctx = UserContext(city='istanbul', interests=['cevre'], disliked_categories=['cevre'])
    disliked_event_ctx = UserContext(city='istanbul', interests=['cevre'], disliked_event_ids={event.id})

    assert engine.score_event(liked_ctx, event).total_score == base_score + 15
    assert engine.score_event(disliked_ctx, event).total_score == base_score - 20
    assert engine.score_event(disliked_event_ctx, event).total_score == base_score - 20


def test_recommend_me_uses_feedback(client):
    org = _setup_org(client)
    event_id = _create_event(client, org, 'Hayvan Barınağı Desteği', category='hayvan')
    token = register_and_login(client, 'fb4@briva.com')
    profile_resp = client.put(
        '/api/volunteers/me',
        json={'first_name': 'Test', 'last_name': 'Gönüllü', 'city': 'Istanbul', 'interests': 'hayvan'},
        headers=auth_header(token),
    )
    assert profile_resp.status_code in (200, 201), profile_resp.get_json()
    client.post(f'/api/feedback/{event_id}', json={'feedback': 'like'}, headers=auth_header(token))

    response = client.get('/api/recommendations/me', headers=auth_header(token))
    assert response.status_code == 200
    recs = response.get_json()['recommendations']
    assert recs, 'Öneri dönmesi bekleniyordu'
    assert recs[0]['breakdown'].get('feedback') == 15


# ---------------- #17: Bildirimler ----------------

def test_notification_created_on_application_approval(client):
    org_token = _setup_org(client)
    event_id = _create_event(client, org_token, 'Bildirimli Etkinlik')
    vol_token = register_and_login(client, 'notif1@briva.com')

    apply_resp = client.post(f'/api/events/{event_id}/apply', json={}, headers=auth_header(vol_token))
    assert apply_resp.status_code == 201, apply_resp.get_json()
    application_id = apply_resp.get_json()['application']['id']

    update = client.put(
        f'/api/applications/{application_id}',
        json={'status': 'approved'},
        headers=auth_header(org_token),
    )
    assert update.status_code == 200

    notifications = client.get('/api/notifications', headers=auth_header(vol_token))
    body = notifications.get_json()
    assert body['unread_count'] == 1
    assert 'onayland' in body['notifications'][0]['message']


def test_mark_notification_read(client):
    org_token = _setup_org(client)
    event_id = _create_event(client, org_token, 'Okundu Testi')
    vol_token = register_and_login(client, 'notif2@briva.com')
    apply_resp = client.post(f'/api/events/{event_id}/apply', json={}, headers=auth_header(vol_token))
    application_id = apply_resp.get_json()['application']['id']
    client.put(f'/api/applications/{application_id}', json={'status': 'rejected'}, headers=auth_header(org_token))

    listing = client.get('/api/notifications', headers=auth_header(vol_token)).get_json()
    notif_id = listing['notifications'][0]['id']

    assert client.put(f'/api/notifications/{notif_id}/read', headers=auth_header(vol_token)).status_code == 200
    after = client.get('/api/notifications', headers=auth_header(vol_token)).get_json()
    assert after['unread_count'] == 0


# ---------------- #18: Etkinlik olustururken otomatik AI analizi ----------------

def test_create_event_returns_ai_analysis(client, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    org = _setup_org(client, email='stk-ai@briva.com')
    response = client.post(
        '/api/events',
        json={'title': 'Kisa', 'start_date': '2026-08-20T10:00:00'},
        headers=auth_header(org),
    )
    assert response.status_code == 201
    body = response.get_json()
    assert 'ai_analysis' in body
    assert set(body['ai_analysis']).issuperset({'score', 'warnings', 'suggestions'})
    assert body['ai_analysis']['warnings'], 'Eksik alanlar icin uyari beklenirdi'
