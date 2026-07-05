from datetime import datetime, timezone
from app.extensions import db

class EventApplication(db.Model):
    __tablename__ = 'event_applications'
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_user_event'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    cover_letter = db.Column(db.Text, nullable=True)
    reviewer_note = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    user = db.relationship('User', back_populates='applications')
    event = db.relationship('Event', back_populates='applications')

    def to_dict(self, include_user: bool=False, include_event: bool=False) -> dict:
        data = {'id': self.id, 'user_id': self.user_id, 'event_id': self.event_id, 'status': self.status, 'cover_letter': self.cover_letter, 'reviewer_note': self.reviewer_note, 'applied_at': self.applied_at.isoformat(), 'updated_at': self.updated_at.isoformat()}
        if include_user and self.user:
            vp = self.user.volunteer_profile
            data['volunteer'] = {'user_id': self.user_id, 'email': self.user.email, 'full_name': vp.full_name if vp else None}
        if include_event and self.event:
            data['event'] = {'id': self.event.id, 'title': self.event.title, 'start_date': self.event.start_date.isoformat()}
        return data

    def __repr__(self) -> str:
        return f'<EventApplication id={self.id} user={self.user_id} event={self.event_id} status={self.status}>'