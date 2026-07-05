from datetime import datetime, timezone
from app.extensions import db

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    max_volunteers = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='published')
    requirements = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    organization = db.relationship('Organization', back_populates='events')
    applications = db.relationship('EventApplication', back_populates='event', cascade='all, delete-orphan')

    @property
    def approved_count(self) -> int:
        return sum((1 for a in self.applications if a.status == 'approved'))

    @property
    def is_full(self) -> bool:
        if self.max_volunteers is None:
            return False
        return self.approved_count >= self.max_volunteers

    def to_dict(self, include_applications: bool=False) -> dict:
        data = {'id': self.id, 'organization_id': self.organization_id, 'organization_name': self.organization.name if self.organization else None, 'title': self.title, 'description': self.description, 'category': self.category, 'city': self.city, 'address': self.address, 'start_date': self.start_date.isoformat(), 'end_date': self.end_date.isoformat() if self.end_date else None, 'max_volunteers': self.max_volunteers, 'approved_count': self.approved_count, 'is_full': self.is_full, 'status': self.status, 'requirements': self.requirements, 'created_at': self.created_at.isoformat()}
        if include_applications:
            data['applications'] = [a.to_dict() for a in self.applications]
        return data

    def __repr__(self) -> str:
        return f'<Event id={self.id} title={self.title} status={self.status}>'