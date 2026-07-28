"""Gamification Engine testleri (issue #38, madde 21).

Kapsam: XP kuralları, idempotency, seviye eşikleri, rozetler,
leaderboard sıralaması/privacy ve güvenlik (401/403, client XP manipülasyonu).
"""
from app.services.gamification import LEVEL_THRESHOLDS, calculate_level
from tests.conftest import auth_header, register_and_login


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

COMPLETE_PROFILE = {
    'first_name': 'Serdar',
    'last_name': 'Test',
    'city': 'Istanbul',
    'bio': 'Gönüllülük seven bir geliştirici.',
    'skills': 'python',
    'interests': 'cevre',
}


def _setup_org(client, email='stk-gam@briva.com'):
    token = register_and_login(client, email, role='organization')
    client.post('/api/organizations', json={'name': 'Gam STK', 'city': 'Istanbul'}, headers=auth_header(token))
    return token


def _create_event(client, org_token, title='Gamification Etkinliği'):
    response = client.post(
        '/api/events',
        json={'title': title, 'start_date': '2026-09-01T10:00:00', 'city': 'Istanbul', 'category': 'cevre'},
        headers=auth_header(org_token),
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()['event']['id']


def _me(client, token) -> dict:
    response = client.get('/api/gamification/me', headers=auth_header(token))
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _apply(client, token, event_id):
    return client.post(f'/api/events/{event_id}/apply', json={}, headers=auth_header(token))


def _set_status(client, org_token, application_id, status):
    return client.put(
        f'/api/applications/{application_id}', json={'status': status}, headers=auth_header(org_token)
    )


# ---------------------------------------------------------------------------
# XP testleri
# ---------------------------------------------------------------------------

def test_profile_complete_awards_20_xp_once(client):
    token = register_and_login(client, 'gam1@briva.com')
    client.put('/api/volunteers/me', json=COMPLETE_PROFILE, headers=auth_header(token))
    assert _me(client, token)['xp'] == 20
    # Tekrar güncelleme XP'yi ikilemez
    client.put('/api/volunteers/me', json={'bio': 'Güncellendi ama hâlâ tamam.'}, headers=auth_header(token))
    assert _me(client, token)['xp'] == 20


def test_incomplete_profile_awards_no_xp(client):
    token = register_and_login(client, 'gam2@briva.com')
    client.put('/api/volunteers/me', json={'first_name': 'Eksik', 'last_name': 'Profil'}, headers=auth_header(token))
    assert _me(client, token)['xp'] == 0


def test_application_created_awards_5_xp_and_duplicate_blocked(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    token = register_and_login(client, 'gam3@briva.com')
    assert _apply(client, token, event_id).status_code == 201
    assert _me(client, token)['xp'] == 5
    # Duplicate başvuru 409 döner ve XP artmaz
    assert _apply(client, token, event_id).status_code == 409
    assert _me(client, token)['xp'] == 5


def test_application_accepted_awards_10_xp_no_duplicate_on_retry(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    token = register_and_login(client, 'gam4@briva.com')
    application_id = _apply(client, token, event_id).get_json()['application']['id']
    assert _set_status(client, org, application_id, 'approved').status_code == 200
    assert _me(client, token)['xp'] == 5 + 10
    # approved → approved tekrarında XP ikilenmez
    _set_status(client, org, application_id, 'approved')
    assert _me(client, token)['xp'] == 15


def test_event_completed_awards_50_xp(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    token = register_and_login(client, 'gam5@briva.com')
    application_id = _apply(client, token, event_id).get_json()['application']['id']
    _set_status(client, org, application_id, 'approved')
    assert _set_status(client, org, application_id, 'completed').status_code == 200
    me = _me(client, token)
    assert me['xp'] == 5 + 10 + 50
    assert me['completed_events'] == 1


def test_completed_requires_approved_first(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    token = register_and_login(client, 'gam6@briva.com')
    application_id = _apply(client, token, event_id).get_json()['application']['id']
    # pending → completed geçişi yasak (sahte katılım engeli, #38 madde 18)
    assert _set_status(client, org, application_id, 'completed').status_code == 400


def test_client_cannot_push_xp(client):
    """İstemciden XP kabul eden bir endpoint YOKTUR (#38 madde 4 ve 22)."""
    token = register_and_login(client, 'gam7@briva.com')
    response = client.post('/api/gamification/add-xp', json={'xp': 500}, headers=auth_header(token))
    assert response.status_code in (404, 405)


# ---------------------------------------------------------------------------
# Seviye testleri
# ---------------------------------------------------------------------------

def test_level_thresholds():
    assert calculate_level(0)['level'] == 1
    assert calculate_level(99)['level'] == 1
    assert calculate_level(100)['level'] == 2
    assert calculate_level(250)['level'] == 3
    assert calculate_level(7500)['level'] == 10


def test_level_progress_and_next_level():
    info = calculate_level(175)  # Level 2 (100) → Level 3 (250) arası yarı yol
    assert info['level'] == 2
    assert info['current_level_xp'] == 100
    assert info['next_level_xp'] == 250
    assert info['progress'] == 0.5
    top = calculate_level(LEVEL_THRESHOLDS[-1] + 100)
    assert top['level'] == 10
    assert top['next_level_xp'] is None
    assert top['progress'] == 1.0


# ---------------------------------------------------------------------------
# Rozet testleri
# ---------------------------------------------------------------------------

def test_first_application_badge(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    token = register_and_login(client, 'gam8@briva.com')
    _apply(client, token, event_id)
    codes = {b['code'] for b in _me(client, token)['badges']}
    assert 'FIRST_APPLICATION' in codes


def test_profile_complete_badge(client):
    token = register_and_login(client, 'gam9@briva.com')
    client.put('/api/volunteers/me', json=COMPLETE_PROFILE, headers=auth_header(token))
    codes = {b['code'] for b in _me(client, token)['badges']}
    assert 'PROFILE_COMPLETE' in codes


def test_first_completion_badge_and_no_duplicates(client):
    org = _setup_org(client)
    token = register_and_login(client, 'gam10@briva.com')
    event_id = _create_event(client, org, 'Rozet Etkinliği')
    application_id = _apply(client, token, event_id).get_json()['application']['id']
    _set_status(client, org, application_id, 'approved')
    _set_status(client, org, application_id, 'completed')
    badges = _me(client, token)['badges']
    codes = [b['code'] for b in badges]
    assert 'FIRST_COMPLETION' in codes
    assert len(codes) == len(set(codes)), 'Duplicate rozet oluşmamalı'


def test_five_completions_badge(client):
    org = _setup_org(client)
    token = register_and_login(client, 'gam11@briva.com')
    for index in range(5):
        event_id = _create_event(client, org, f'Seri Etkinlik {index}')
        application_id = _apply(client, token, event_id).get_json()['application']['id']
        _set_status(client, org, application_id, 'approved')
        _set_status(client, org, application_id, 'completed')
    me = _me(client, token)
    codes = {b['code'] for b in me['badges']}
    assert 'FIVE_COMPLETIONS' in codes
    assert me['completed_events'] == 5
    assert me['xp'] == 5 * (5 + 10 + 50)


# ---------------------------------------------------------------------------
# Leaderboard testleri
# ---------------------------------------------------------------------------

def test_leaderboard_ranking_and_privacy(client):
    org = _setup_org(client)
    event_id = _create_event(client, org)
    low_token = register_and_login(client, 'lb-low@briva.com')
    high_token = register_and_login(client, 'lb-high@briva.com')
    client.put('/api/volunteers/me', json={**COMPLETE_PROFILE, 'first_name': 'Yüksek'}, headers=auth_header(high_token))  # +20
    application_id = _apply(client, high_token, event_id).get_json()['application']['id']  # +5
    _set_status(client, org, application_id, 'approved')  # +10
    _apply(client, low_token, event_id)  # +5

    body = client.get('/api/gamification/leaderboard', headers=auth_header(low_token)).get_json()
    entries = body['entries']
    assert entries[0]['xp'] == 35
    assert entries[0]['display_name'] == 'Yüksek'
    assert entries[0]['rank'] == 1
    assert body['current_user']['xp'] == 5
    assert body['current_user']['rank'] == 2
    # Privacy: email veya hassas alan sızmıyor
    for entry in entries:
        assert set(entry.keys()) == {'rank', 'user_id', 'display_name', 'xp'}


def test_leaderboard_requires_auth(client):
    assert client.get('/api/gamification/leaderboard').status_code == 401


# ---------------------------------------------------------------------------
# Güvenlik testleri
# ---------------------------------------------------------------------------

def test_me_requires_auth_and_volunteer_role(client):
    assert client.get('/api/gamification/me').status_code == 401
    org_token = _setup_org(client, email='stk-403@briva.com')
    assert client.get('/api/gamification/me', headers=auth_header(org_token)).status_code == 403
    assert client.get('/api/gamification/me/history', headers=auth_header(org_token)).status_code == 403


def test_history_pagination(client):
    org = _setup_org(client)
    token = register_and_login(client, 'gam12@briva.com')
    for index in range(3):
        event_id = _create_event(client, org, f'Sayfa Etkinliği {index}')
        _apply(client, token, event_id)
    body = client.get('/api/gamification/me/history?page=1&per_page=2', headers=auth_header(token)).get_json()
    assert body['total'] == 3
    assert len(body['items']) == 2
    assert body['page'] == 1
    page2 = client.get('/api/gamification/me/history?page=2&per_page=2', headers=auth_header(token)).get_json()
    assert len(page2['items']) == 1
