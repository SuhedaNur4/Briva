from datetime import datetime, timezone
from app.extensions import db


class XPTransaction(db.Model):
    """XP hareketlerinin değiştirilemez denetim izi (issue #38, #30).

    Toplam XP her zaman bu tablodaki kayıtların toplamından doğrulanabilir.
    (user_id, event_type, source_type, source_id) unique kısıtı sayesinde
    aynı olay (örn. Application #100 kabulü) birden fazla kez işlense bile
    XP yalnızca bir kez üretilir (idempotency).
    """

    __tablename__ = 'xp_transactions'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_type', 'source_type', 'source_id', name='uq_xp_event_source'),
        db.Index('ix_xp_user_created', 'user_id', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)   # PROFILE_COMPLETED | APPLICATION_CREATED | APPLICATION_ACCEPTED | EVENT_COMPLETED
    source_type = db.Column(db.String(50), nullable=False)  # profile | application | event
    source_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='xp_transactions')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'amount': self.amount,
            'reason': self.reason,
            'event_type': self.event_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f'<XPTransaction id={self.id} user={self.user_id} amount={self.amount} event={self.event_type}>'
