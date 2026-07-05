import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-please-change")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///briva.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "jwt-secret-please-change")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600)
    )
    # Varsayılan CORS ayarı
    CORS_ORIGINS: list = os.environ.get("CORS_ORIGINS", "*").split(",")
    # Rate Limiting
    RATELIMIT_DEFAULT: str = os.environ.get("RATELIMIT_DEFAULT", "200 per day, 50 per hour")

class DevelopmentConfig(Config):
    DEBUG: bool = True

class ProductionConfig(Config):
    DEBUG: bool = False
    # Üretimde güvenlik için strict kontroller
    def __init__(self):
        if self.SECRET_KEY == "dev-secret-key-please-change":
            raise ValueError("Production: SECRET_KEY is not securely set!")
        if self.JWT_SECRET_KEY == "jwt-secret-please-change":
            raise ValueError("Production: JWT_SECRET_KEY is not securely set!")
        if "*" in self.CORS_ORIGINS:
            raise ValueError("Production: CORS_ORIGINS must not be '*'")

class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
config_map: dict = {'development': DevelopmentConfig, 'production': ProductionConfig, 'testing': TestingConfig}

def get_config() -> Config:
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)