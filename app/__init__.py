from flask import Flask, jsonify
from flask_talisman import Talisman

from app.config import get_config
from app.extensions import db, jwt, cors, limiter

def create_app(config_override=None) -> Flask:
    flask_app = Flask(__name__, instance_relative_config=True)
    config = config_override or get_config()
    flask_app.config.from_object(config)
    db.init_app(flask_app)
    jwt.init_app(flask_app)
    cors.init_app(flask_app, resources={r"/api/*": {"origins": flask_app.config["CORS_ORIGINS"]}})
    
    # Güvenlik Eklentileri
    limiter.init_app(flask_app)
    
    # Talisman - Security Headers
    # API olduğu için content_security_policy kapatıldı, HTTPS zorunluluğu prod için eklendi.
    Talisman(
        flask_app,
        force_https=not flask_app.config["DEBUG"],
        content_security_policy=None,
        session_cookie_secure=not flask_app.config["DEBUG"]
    )
    _register_blueprints(flask_app)
    with flask_app.app_context():
        from app import models
        db.create_all()
    _register_error_handlers(flask_app)
    return flask_app

def _register_blueprints(flask_app: Flask) -> None:
    from app.routes.auth import auth_bp
    from app.routes.volunteers import volunteers_bp
    from app.routes.organizations import organizations_bp
    from app.routes.events import events_bp
    from app.routes.applications import applications_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.favorites import favorites_bp
    from app.routes.ai import ai_bp
    from app.routes.feedback import feedback_bp
    from app.routes.notifications import notifications_bp
    flask_app.register_blueprint(auth_bp, url_prefix='/api/auth')
    flask_app.register_blueprint(volunteers_bp, url_prefix='/api/volunteers')
    flask_app.register_blueprint(organizations_bp, url_prefix='/api/organizations')
    flask_app.register_blueprint(events_bp, url_prefix='/api/events')
    flask_app.register_blueprint(applications_bp, url_prefix='/api/applications')
    flask_app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    flask_app.register_blueprint(favorites_bp, url_prefix='/api/favorites')
    flask_app.register_blueprint(ai_bp, url_prefix='/api/ai')
    flask_app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    flask_app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    # Swagger UI Blueprint
    from flask_swagger_ui import get_swaggerui_blueprint
    SWAGGER_URL = '/docs'
    API_URL = '/static/swagger.json'
    swaggerui_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Briva API"
        }
    )
    flask_app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

def _register_error_handlers(flask_app: Flask) -> None:

    @flask_app.errorhandler(400)
    def bad_request(e):
        return (jsonify({'error': 'Geçersiz istek', 'detail': str(e)}), 400)

    @flask_app.errorhandler(401)
    def unauthorized(e):
        return (jsonify({'error': 'Yetkisiz erişim'}), 401)

    @flask_app.errorhandler(403)
    def forbidden(e):
        return (jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403)

    @flask_app.errorhandler(404)
    def not_found(e):
        return (jsonify({'error': 'Kaynak bulunamadı'}), 404)

    @flask_app.errorhandler(409)
    def conflict(e):
        return (jsonify({'error': 'Çakışma', 'detail': str(e)}), 409)

    @flask_app.errorhandler(500)
    def internal_error(e):
        return (jsonify({'error': 'Sunucu hatası'}), 500)