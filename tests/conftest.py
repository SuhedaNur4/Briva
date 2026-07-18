import pytest

from app import create_app
from app.extensions import db as _db


class _TestConfig:
    TESTING = True
    DEBUG = True  # Talisman'ın HTTPS zorlamasını test ortamında kapatır
    SECRET_KEY = 'test-secret'
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ['*']
    RATELIMIT_ENABLED = False


@pytest.fixture()
def app():
    application = create_app(config_override=_TestConfig)
    with application.app_context():
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, email: str, role: str = 'volunteer') -> str:
    """Kullanıcı kaydeder, giriş yapar ve access token döner."""
    client.post('/api/auth/register', json={'email': email, 'password': 'Test1234!', 'role': role})
    response = client.post('/api/auth/login', json={'email': email, 'password': 'Test1234!'})
    return response.get_json()['access_token']


def auth_header(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}
