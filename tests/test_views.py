def test_index_view(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Briva' in response.data
    assert b'<!DOCTYPE html>' in response.data

def test_events_view(client):
    response = client.get('/events')
    assert response.status_code == 200
    assert b'G\xc3\xb6n\xc3\xbcll\xc3\xbcl\xc3\xbck Etkinlikleri' in response.data

def test_event_detail_view(client):
    response = client.get('/events/1')
    assert response.status_code == 200
    assert b'data-event-id="1"' in response.data

def test_volunteer_dashboard_view(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'G\xc3\xb6n\xc3\xbcll\xc3\xbc Kontrol Paneli' in response.data

def test_organization_dashboard_view(client):
    response = client.get('/organization/dashboard')
    assert response.status_code == 200
    assert b'STK Y\xc3\xb6netim Paneli' in response.data

def test_organization_event_new_view(client):
    response = client.get('/organization/events/new')
    assert response.status_code == 200
    assert b'Yeni G\xc3\xb6n\xc3\xbcll\xc3\xbcl\xc3\xbck Etkinli\xc4\x9fi' in response.data

def test_organization_profile_view(client):
    response = client.get('/organizations/1')
    assert response.status_code == 200
    assert b'data-org-id="1"' in response.data
