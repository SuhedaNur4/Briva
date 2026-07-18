from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.volunteer import VolunteerProfile
    from app.models.event import Event
SCORE_CITY_MATCH: int = 40
SCORE_INTEREST_MATCH: int = 30
SCORE_SKILL_MATCH: int = 20
SCORE_DAY_MATCH: int = 10
SCORE_FEEDBACK_LIKE: int = 15    # Kullanıcı beğendiyse bonus (issue #19)
SCORE_FEEDBACK_DISLIKE: int = -20  # Kullanıcı beğenmediyse ceza (issue #19)
RECOMMENDATION_THRESHOLD: int = 70
MAX_RECOMMENDATIONS: int = 20

@dataclass
class UserContext:
    city: str = ''
    interests: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    available_days: list[str] = field(default_factory=list)
    liked_categories: list[str] = field(default_factory=list)
    disliked_categories: list[str] = field(default_factory=list)
    liked_event_ids: set = field(default_factory=set)
    disliked_event_ids: set = field(default_factory=set)

    @classmethod
    def from_volunteer_profile(cls, profile: 'VolunteerProfile') -> 'UserContext':
        return cls(city=_normalize_str(profile.city or ''), interests=_normalize_list(profile.interests_list), skills=_normalize_list(profile.skills_list), available_days=_normalize_list(getattr(profile, 'available_days_list', [])))

    def with_feedback(self, liked_categories: list[str], disliked_categories: list[str],
                      liked_event_ids: set | None = None, disliked_event_ids: set | None = None) -> 'UserContext':
        """Kullanıcının geçmiş geri bildirim sinyallerini bağlama ekler (issue #19)."""
        self.liked_categories = _normalize_list(liked_categories)
        self.disliked_categories = _normalize_list(disliked_categories)
        self.liked_event_ids = set(liked_event_ids or set())
        self.disliked_event_ids = set(disliked_event_ids or set())
        return self

    @classmethod
    def from_dict(cls, data: dict) -> 'UserContext':
        return cls(city=_normalize_str(data.get('city', '')), interests=_normalize_list(data.get('interests', [])), skills=_normalize_list(data.get('skills', [])), available_days=_normalize_list(data.get('available_days', [])), liked_categories=_normalize_list(data.get('liked_categories', [])), disliked_categories=_normalize_list(data.get('disliked_categories', [])))

@dataclass
class EventScore:
    event_id: int
    event_title: str
    total_score: int
    breakdown: dict[str, int]
    matching_details: dict[str, list]
    event_data: dict

    def to_dict(self) -> dict:
        return {'event_id': self.event_id, 'event_title': self.event_title, 'total_score': self.total_score, 'breakdown': self.breakdown, 'matching_details': self.matching_details, 'event': self.event_data}

def _normalize_str(value: str) -> str:
    value = value.replace('İ', 'i').replace('I', 'i')
    result = value.strip().lower()
    replacements = {'ğ': 'g', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ü': 'u', 'ş': 's', 'ç': 'c'}
    for tr_char, ascii_char in replacements.items():
        result = result.replace(tr_char, ascii_char)
    return result

def _normalize_list(items: list) -> list[str]:
    return [_normalize_str(item) for item in items if item and str(item).strip()]

def _parse_day_of_week(dt: datetime) -> str:
    return dt.strftime('%A').lower()

def _score_city(user: UserContext, event_city: str) -> tuple[int, bool]:
    if not user.city or not event_city:
        return (0, False)
    matched = user.city == _normalize_str(event_city)
    return (SCORE_CITY_MATCH if matched else 0, matched)

def _score_interests(user: UserContext, event_category: str) -> tuple[int, list[str]]:
    if not user.interests or not event_category:
        return (0, [])
    norm_category = _normalize_str(event_category)
    matching = [interest for interest in user.interests if interest in norm_category or norm_category in interest]
    score = len(matching) * SCORE_INTEREST_MATCH
    return (score, matching)

def _score_skills(user: UserContext, event_requirements: str) -> tuple[int, list[str]]:
    if not user.skills or not event_requirements:
        return (0, [])
    norm_req = _normalize_str(event_requirements)
    matching = [skill for skill in user.skills if skill in norm_req]
    score = len(matching) * SCORE_SKILL_MATCH
    return (score, matching)

def _score_available_days(user: UserContext, event_start: datetime) -> tuple[int, bool]:
    if not user.available_days or not event_start:
        return (0, False)
    event_day = _parse_day_of_week(event_start)
    matched = event_day in user.available_days
    return (SCORE_DAY_MATCH if matched else 0, matched)

def _score_feedback(user: UserContext, event_id: int, event_category: str) -> tuple[int, str]:
    """Geçmiş geri bildirimlere göre ödül/ceza uygular (issue #19).

    1) Etkinliğe doğrudan verilmiş feedback varsa o kullanılır (spec'teki davranış).
    2) Yoksa aynı kategorideki geçmiş like/dislike sinyalleri genellenir —
       böylece motor, kullanıcının beğenmediği kategorileri de öğrenir.
    """
    if event_id in user.disliked_event_ids:
        return (SCORE_FEEDBACK_DISLIKE, 'disliked_event')
    if event_id in user.liked_event_ids:
        return (SCORE_FEEDBACK_LIKE, 'liked_event')
    if not event_category:
        return (0, 'none')
    norm_category = _normalize_str(event_category)
    if any(cat in norm_category or norm_category in cat for cat in user.disliked_categories):
        return (SCORE_FEEDBACK_DISLIKE, 'disliked_category')
    if any(cat in norm_category or norm_category in cat for cat in user.liked_categories):
        return (SCORE_FEEDBACK_LIKE, 'liked_category')
    return (0, 'none')


class RecommendationEngine:

    def __init__(self, threshold: int=RECOMMENDATION_THRESHOLD, max_results: int=MAX_RECOMMENDATIONS):
        self.threshold = threshold
        self.max_results = max_results

    def score_event(self, user: UserContext, event: 'Event') -> EventScore:
        breakdown: dict[str, int] = {}
        matching_details: dict[str, list] = {}
        city_score, city_matched = _score_city(user, event.city or '')
        breakdown['city'] = city_score
        matching_details['city_matched'] = city_matched
        interest_score, matching_interests = _score_interests(user, event.category or '')
        breakdown['interests'] = interest_score
        matching_details['matching_interests'] = matching_interests
        skill_score, matching_skills = _score_skills(user, event.requirements or '')
        breakdown['skills'] = skill_score
        matching_details['matching_skills'] = matching_skills
        day_score, day_matched = _score_available_days(user, event.start_date)
        breakdown['available_day'] = day_score
        matching_details['day_matched'] = day_matched
        feedback_score, feedback_signal = _score_feedback(user, event.id, event.category or '')
        breakdown['feedback'] = feedback_score
        matching_details['feedback_signal'] = feedback_signal
        total = sum(breakdown.values())
        return EventScore(event_id=event.id, event_title=event.title, total_score=total, breakdown=breakdown, matching_details=matching_details, event_data=event.to_dict())

    def recommend(self, user: UserContext, events: list['Event']) -> list[EventScore]:
        now = datetime.now(timezone.utc)
        results: list[EventScore] = []
        for event in events:
            if event.status != 'published':
                continue
            if event.is_full:
                continue
            event_start = event.start_date
            if event_start.tzinfo is None:
                event_start = event_start.replace(tzinfo=timezone.utc)
            if event_start <= now:
                continue
            scored = self.score_event(user, event)
            if scored.total_score >= self.threshold:
                results.append(scored)
        results.sort(key=lambda r: r.total_score, reverse=True)
        return results[:self.max_results]

    def explain(self, user: UserContext, event: 'Event') -> dict:
        scored = self.score_event(user, event)
        return {'event_id': scored.event_id, 'event_title': scored.event_title, 'total_score': scored.total_score, 'threshold': self.threshold, 'recommended': scored.total_score >= self.threshold, 'breakdown': scored.breakdown, 'details': scored.matching_details, 'scoring_rules': {'city_match': f'+{SCORE_CITY_MATCH} puan', 'interest_match': f'+{SCORE_INTEREST_MATCH} puan (her eşleşen alan için)', 'skill_match': f'+{SCORE_SKILL_MATCH} puan (her eşleşen beceri için)', 'day_match': f'+{SCORE_DAY_MATCH} puan', 'feedback_like': f'+{SCORE_FEEDBACK_LIKE} puan (beğendiğiniz etkinlik/kategorilerde)', 'feedback_dislike': f'{SCORE_FEEDBACK_DISLIKE} puan (beğenmediğiniz etkinlik/kategorilerde)'}}
engine = RecommendationEngine()