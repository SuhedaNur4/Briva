from datetime import datetime, timezone
from app.extensions import db

class VolunteerProfile(db.Model):
    __tablename__ = 'volunteer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    user = db.relationship('User', back_populates='volunteer_profile')

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def interests_list(self) -> list:
        if not self.interests:
            return []
        return [i.strip() for i in self.interests.split(',') if i.strip()]

    @property
    def skills_list(self) -> list:
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def to_dict(self) -> dict:
        return {'id': self.id, 'user_id': self.user_id, 'first_name': self.first_name, 'last_name': self.last_name, 'full_name': self.full_name, 'phone': self.phone, 'birth_date': self.birth_date.isoformat() if self.birth_date else None, 'city': self.city, 'bio': self.bio, 'interests': self.interests_list, 'skills': self.skills_list, 'created_at': self.created_at.isoformat()}

    def __repr__(self) -> str:
        return f'<VolunteerProfile id={self.id} user_id={self.user_id} name={self.full_name}>'