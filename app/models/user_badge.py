from datetime import datetime, timezone
from app.extensions import db


class UserBadge(db.Model):
    """Kullanıcının kazandığı rozetler (issue #38). Aynı rozet ikinci kez kazanılamaz."""

    __tablename__ = 'user_badges'
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False, index=True)
    earned_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='badges')
    badge = db.relationship('Badge', back_populates='user_badges')

    def to_dict(self) -> dict:
        data = self.badge.to_dict() if self.badge else {}
        data['earned_at'] = self.earned_at.isoformat()
        return data

    def __repr__(self) -> str:
        return f'<UserBadge id={self.id} user={self.user_id} badge={self.badge_id}>'
