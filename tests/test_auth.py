from tests.conftest import auth_header, register_and_login


def test_register_creates_user_and_returns_token(client):
    response = client.post(
        '/api/auth/register',
        json={'email': 'yeni@briva.com', 'password': 'Test1234!', 'role': 'volunteer'},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert 'access_token' in body
    assert body['user']['email'] == 'yeni@briva.com'


def test_register_duplicate_email_returns_409(client):
    payload = {'email': 'ayni@briva.com', 'password': 'Test1234!', 'role': 'volunteer'}
    assert client.post('/api/auth/register', json=payload).status_code == 201
    assert client.post('/api/auth/register', json=payload).status_code == 409


def test_login_with_wrong_password_returns_401(client):
    client.post(
        '/api/auth/register',
        json={'email': 'kul@briva.com', 'password': 'Test1234!', 'role': 'volunteer'},
    )
    response = client.post(
        '/api/auth/login', json={'email': 'kul@briva.com', 'password': 'Yanlis123!'}
    )
    assert response.status_code == 401


def test_me_requires_jwt(client):
    assert client.get('/api/auth/me').status_code == 401


def test_me_returns_current_user(client):
    token = register_and_login(client, 'ben@briva.com')
    response = client.get('/api/auth/me', headers=auth_header(token))
    assert response.status_code == 200
    assert response.get_json()['user']['email'] == 'ben@briva.com'
