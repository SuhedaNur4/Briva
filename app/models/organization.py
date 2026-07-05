from datetime import datetime, timezone
from app.extensions import db

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    user = db.relationship('User', back_populates='organization')
    events = db.relationship('Event', back_populates='organization', cascade='all, delete-orphan')

    def to_dict(self, include_events: bool=False) -> dict:
        data = {'id': self.id, 'user_id': self.user_id, 'name': self.name, 'description': self.description, 'website': self.website, 'phone': self.phone, 'address': self.address, 'city': self.city, 'is_verified': self.is_verified, 'created_at': self.created_at.isoformat()}
        if include_events:
            data['events'] = [e.to_dict() for e in self.events]
        return data

    def __repr__(self) -> str:
        return f'<Organization id={self.id} name={self.name}>'