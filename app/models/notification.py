from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    """Kullanıcı bildirimleri (Sprint 2 — şema modellemesi).

    Örn. başvuru onaylandığında/reddedildiğinde gönüllüye bildirim düşer.
    """

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notif_type = db.Column(db.String(50), nullable=False, default='general')
    message = db.Column(db.Text, nullable=False)
    related_event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='notifications')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notif_type': self.notif_type,
            'message': self.message,
            'related_event_id': self.related_event_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f'<Notification id={self.id} user={self.user_id} type={self.notif_type} read={self.is_read}>'
