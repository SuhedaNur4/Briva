from tests.conftest import auth_header, register_and_login


def _create_event(client) -> int:
    """Yardımcı: STK kullanıcısı + profil + etkinlik oluşturur, event id döner."""
    org_token = register_and_login(client, 'stk@briva.com', role='organization')
    client.post(
        '/api/organizations',
        json={'name': 'Test STK', 'city': 'Istanbul'},
        headers=auth_header(org_token),
    )
    response = client.post(
        '/api/events',
        json={
            'title': 'Sahil Temizliği Etkinliği',
            'start_date': '2026-08-15T09:00:00',
            'city': 'Istanbul',
            'category': 'cevre',
        },
        headers=auth_header(org_token),
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()['event']['id']


def test_volunteer_can_add_and_list_favorites(client):
    event_id = _create_event(client)
    token = register_and_login(client, 'gonullu@briva.com')

    add = client.post(f'/api/favorites/{event_id}', headers=auth_header(token))
    assert add.status_code == 201

    listing = client.get('/api/favorites', headers=auth_header(token))
    assert listing.status_code == 200
    body = listing.get_json()
    assert body['total'] == 1
    assert body['favorites'][0]['event_id'] == event_id


def test_duplicate_favorite_returns_409(client):
    event_id = _create_event(client)
    token = register_and_login(client, 'gonullu2@briva.com')
    assert client.post(f'/api/favorites/{event_id}', headers=auth_header(token)).status_code == 201
    assert client.post(f'/api/favorites/{event_id}', headers=auth_header(token)).status_code == 409


def test_remove_favorite(client):
    event_id = _create_event(client)
    token = register_and_login(client, 'gonullu3@briva.com')
    client.post(f'/api/favorites/{event_id}', headers=auth_header(token))

    remove = client.delete(f'/api/favorites/{event_id}', headers=auth_header(token))
    assert remove.status_code == 200

    listing = client.get('/api/favorites', headers=auth_header(token))
    assert listing.get_json()['total'] == 0


def test_favorite_nonexistent_event_returns_404(client):
    token = register_and_login(client, 'gonullu4@briva.com')
    assert client.post('/api/favorites/9999', headers=auth_header(token)).status_code == 404


def test_organization_cannot_add_favorite(client):
    event_id = _create_event(client)
    org_token = register_and_login(client, 'stk2@briva.com', role='organization')
    response = client.post(f'/api/favorites/{event_id}', headers=auth_header(org_token))
    assert response.status_code == 403
