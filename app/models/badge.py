from datetime import datetime, timezone
from app.extensions import db


class Badge(db.Model):
    """Rozet tanımları (issue #38, #29). Varsayılan rozetler GamificationService.seed_badges ile eklenir."""

    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    criteria_type = db.Column(db.String(50), nullable=False)   # application_count | completion_count | profile_complete
    criteria_value = db.Column(db.Integer, nullable=False, default=1)
    icon_key = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user_badges = db.relationship('UserBadge', back_populates='badge', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'criteria_type': self.criteria_type,
            'criteria_value': self.criteria_value,
            'icon_key': self.icon_key,
        }

    def __repr__(self) -> str:
        return f'<Badge id={self.id} code={self.code}>'
