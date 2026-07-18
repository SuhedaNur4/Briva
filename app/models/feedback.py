from datetime import datetime, timezone
from app.extensions import db

FEEDBACK_LIKE = 'like'
FEEDBACK_DISLIKE = 'dislike'
VALID_FEEDBACK_VALUES = (FEEDBACK_LIKE, FEEDBACK_DISLIKE)


class RecommendationFeedback(db.Model):
    """Gönüllülerin önerilere verdiği beğendim/beğenmedim geri bildirimi (Sprint 2).

    Bu geri bildirimler öneri motoruna sinyal olarak geri beslenir:
    beğenilen kategoriler skorda ödüllendirilir, beğenilmeyenler cezalandırılır.
    """

    __tablename__ = 'recommendation_feedbacks'
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_feedback_user_event'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False)  # 'like' | 'dislike' (issue #19 spec)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='feedbacks')
    event = db.relationship('Event', back_populates='feedbacks')

    def to_dict(self, include_event: bool = False) -> dict:
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_event and self.event:
            data['event'] = {
                'id': self.event.id,
                'title': self.event.title,
                'category': self.event.category,
            }
        return data

    def __repr__(self) -> str:
        return f'<RecommendationFeedback id={self.id} user={self.user_id} event={self.event_id} status={self.status}>'
