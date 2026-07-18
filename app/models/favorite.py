from datetime import datetime, timezone
from app.extensions import db


class Favorite(db.Model):
    """Gönüllülerin etkinlikleri favorilere eklemesini sağlayan model (Sprint 2)."""

    __tablename__ = 'favorites'
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_favorite_user_event'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='favorites')
    event = db.relationship('Event', back_populates='favorited_by')

    def to_dict(self, include_event: bool = True) -> dict:
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat(),
        }
        if include_event and self.event:
            data['event'] = self.event.to_dict()
        return data

    def __repr__(self) -> str:
        return f'<Favorite id={self.id} user={self.user_id} event={self.event_id}>'
