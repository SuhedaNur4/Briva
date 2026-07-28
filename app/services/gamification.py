"""Gamification Service (issue #38).

Tüm XP / seviye / rozet / leaderboard mantığı bu serviste toplanır; route
dosyalarına dağıtılmaz. XP yalnızca backend'in doğruladığı domain
olaylarından üretilir — istemciden gelen XP değeri hiçbir koşulda kabul
edilmez (bu yüzden add-xp benzeri bir endpoint yoktur).
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.badge import Badge
from app.models.user_badge import UserBadge
from app.models.volunteer import VolunteerProfile
from app.models.xp_transaction import XPTransaction

# ---------------------------------------------------------------------------
# Merkezi konfigürasyon (#38 madde 3 ve 8) — değerler koda dağıtılmaz
# ---------------------------------------------------------------------------

XP_RULES: dict[str, dict] = {
    'PROFILE_COMPLETED': {'amount': 20, 'reason': 'Profil tamamlandı'},
    'APPLICATION_CREATED': {'amount': 5, 'reason': 'Etkinliğe başvuru yapıldı'},
    'APPLICATION_ACCEPTED': {'amount': 10, 'reason': 'Başvuru kabul edildi'},
    'EVENT_COMPLETED': {'amount': 50, 'reason': 'Etkinlik katılımı tamamlandı'},
}

LEVEL_THRESHOLDS: list[int] = [0, 100, 250, 500, 1000, 1750, 2750, 4000, 5500, 7500]

DEFAULT_BADGES: list[dict] = [
    {'code': 'FIRST_APPLICATION', 'name': 'İlk Adım', 'description': 'İlk etkinlik başvurunu yaptın.', 'criteria_type': 'application_count', 'criteria_value': 1, 'icon_key': 'flag'},
    {'code': 'FIRST_COMPLETION', 'name': 'İlk Katılım', 'description': 'İlk etkinliğini tamamladın.', 'criteria_type': 'completion_count', 'criteria_value': 1, 'icon_key': 'handshake'},
    {'code': 'FIVE_COMPLETIONS', 'name': 'Aktif Gönüllü', 'description': '5 etkinlik tamamladın.', 'criteria_type': 'completion_count', 'criteria_value': 5, 'icon_key': 'seedling'},
    {'code': 'TEN_COMPLETIONS', 'name': 'Deneyimli Gönüllü', 'description': '10 etkinlik tamamladın.', 'criteria_type': 'completion_count', 'criteria_value': 10, 'icon_key': 'star'},
    {'code': 'TWENTY_FIVE_COMPLETIONS', 'name': 'Topluluk Katkısı', 'description': '25 etkinlik tamamladın.', 'criteria_type': 'completion_count', 'criteria_value': 25, 'icon_key': 'trophy'},
    {'code': 'PROFILE_COMPLETE', 'name': 'Profil Hazır', 'description': 'Profilini eksiksiz doldurdun.', 'criteria_type': 'profile_complete', 'criteria_value': 1, 'icon_key': 'user'},
]


def seed_badges() -> None:
    """Varsayılan rozet tanımlarını (yoksa) veritabanına ekler. Idempotenttir."""
    existing_codes = {code for (code,) in db.session.query(Badge.code).all()}
    created = False
    for badge_def in DEFAULT_BADGES:
        if badge_def['code'] not in existing_codes:
            db.session.add(Badge(**badge_def))
            created = True
    if created:
        db.session.commit()


# ---------------------------------------------------------------------------
# XP motoru
# ---------------------------------------------------------------------------

def award_xp(user_id: int, event_type: str, source_type: str, source_id: int) -> XPTransaction | None:
    """Domain olayına karşılık XP üretir. Idempotenttir: aynı olay için ikinci
    çağrı yeni transaction üretmez (önce sorgu, ayrıca DB unique kısıtı).

    Not: commit çağıranın sorumluluğundadır; böylece XP, tetikleyen iş
    kaydıyla aynı transaction içinde yazılır.
    """
    rule = XP_RULES.get(event_type)
    if rule is None:
        return None
    existing = XPTransaction.query.filter_by(
        user_id=user_id, event_type=event_type, source_type=source_type, source_id=source_id
    ).first()
    if existing:
        return None
    transaction = XPTransaction(
        user_id=user_id,
        amount=rule['amount'],
        reason=rule['reason'],
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
    )
    db.session.add(transaction)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return None
    _refresh_cached_xp(user_id)
    check_badges(user_id)
    return transaction


def get_total_xp(user_id: int) -> int:
    """Toplam XP her zaman transaction geçmişinden hesaplanır (tek doğruluk kaynağı)."""
    total = db.session.query(func.coalesce(func.sum(XPTransaction.amount), 0)).filter(
        XPTransaction.user_id == user_id
    ).scalar()
    return int(total or 0)


def _refresh_cached_xp(user_id: int) -> None:
    profile = VolunteerProfile.query.filter_by(user_id=user_id).first()
    if profile is not None:
        profile.xp_points = get_total_xp(user_id)


# ---------------------------------------------------------------------------
# Seviye motoru (#38 madde 8)
# ---------------------------------------------------------------------------

def calculate_level(total_xp: int) -> dict:
    """XP'den seviye, eşikler ve ilerleme oranını hesaplar. Frontend hesap yapmaz."""
    level = 1
    for index, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
        if total_xp >= threshold:
            level = index
    current_level_xp = LEVEL_THRESHOLDS[level - 1]
    next_level_xp = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else None
    if next_level_xp is None:
        progress = 1.0
    else:
        span = next_level_xp - current_level_xp
        progress = round((total_xp - current_level_xp) / span, 2) if span else 1.0
    return {
        'level': level,
        'current_level_xp': current_level_xp,
        'next_level_xp': next_level_xp,
        'progress': progress,
    }


# ---------------------------------------------------------------------------
# Rozet motoru (#38 madde 9-11)
# ---------------------------------------------------------------------------

def _completion_count(user_id: int) -> int:
    from app.models.application import EventApplication
    return EventApplication.query.filter_by(user_id=user_id, status='completed').count()


def _application_count(user_id: int) -> int:
    from app.models.application import EventApplication
    return EventApplication.query.filter_by(user_id=user_id).count()


def is_profile_complete(profile: VolunteerProfile | None) -> bool:
    """Minimum profil (#38 madde 3): ad, soyad, şehir, bio, en az 1 beceri ve 1 ilgi alanı."""
    if profile is None:
        return False
    return all([
        (profile.first_name or '').strip(),
        (profile.last_name or '').strip(),
        (profile.city or '').strip(),
        (profile.bio or '').strip(),
        len(profile.skills_list) >= 1,
        len(profile.interests_list) >= 1,
    ])


def check_badges(user_id: int) -> list[UserBadge]:
    """Rozet kriterlerini kontrol eder, hak edilen yeni rozetleri verir. Duplicate üretmez."""
    earned_ids = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user_id).all()}
    newly_earned: list[UserBadge] = []
    counters: dict[str, int] = {}
    profile = VolunteerProfile.query.filter_by(user_id=user_id).first()
    for badge in Badge.query.filter_by(is_active=True).all():
        if badge.id in earned_ids:
            continue
        if badge.criteria_type == 'application_count':
            counters.setdefault('applications', _application_count(user_id))
            achieved = counters['applications'] >= badge.criteria_value
        elif badge.criteria_type == 'completion_count':
            counters.setdefault('completions', _completion_count(user_id))
            achieved = counters['completions'] >= badge.criteria_value
        elif badge.criteria_type == 'profile_complete':
            achieved = is_profile_complete(profile)
        else:
            achieved = False
        if achieved:
            user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
            db.session.add(user_badge)
            try:
                db.session.flush()
                newly_earned.append(user_badge)
            except IntegrityError:
                db.session.rollback()
    return newly_earned


# ---------------------------------------------------------------------------
# Kullanıcı görünümleri ve leaderboard (#38 madde 12-15)
# ---------------------------------------------------------------------------

def get_user_gamification(user_id: int) -> dict:
    total_xp = get_total_xp(user_id)
    level_info = calculate_level(total_xp)
    user_badges = (
        UserBadge.query.filter_by(user_id=user_id)
        .join(Badge)
        .order_by(UserBadge.earned_at.asc())
        .all()
    )
    return {
        'xp': total_xp,
        **level_info,
        'completed_events': _completion_count(user_id),
        'applications': _application_count(user_id),
        'badges': [ub.to_dict() for ub in user_badges],
    }


def get_xp_history(user_id: int, page: int = 1, per_page: int = 20) -> dict:
    pagination = (
        XPTransaction.query.filter_by(user_id=user_id)
        .order_by(XPTransaction.created_at.desc(), XPTransaction.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        'items': [t.to_dict() for t in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
    }


def get_leaderboard(limit: int = 10, current_user_id: int | None = None) -> dict:
    """All-time leaderboard. Tek sorguda SUM + GROUP BY (N+1 yok); yalnızca
    public bilgiler döner (#38 madde 13). Eşit XP'de user_id ile deterministik.
    """
    totals = (
        db.session.query(
            XPTransaction.user_id.label('user_id'),
            func.sum(XPTransaction.amount).label('xp'),
        )
        .group_by(XPTransaction.user_id)
        .order_by(func.sum(XPTransaction.amount).desc(), XPTransaction.user_id.asc())
        .all()
    )
    profiles = {
        p.user_id: p
        for p in VolunteerProfile.query.filter(
            VolunteerProfile.user_id.in_([row.user_id for row in totals])
        ).all()
    } if totals else {}
    entries = []
    current_user_block = None
    for rank, row in enumerate(totals, start=1):
        profile = profiles.get(row.user_id)
        display_name = profile.first_name if profile else f'Gönüllü #{row.user_id}'
        if rank <= limit:
            entries.append({
                'rank': rank,
                'user_id': row.user_id,
                'display_name': display_name,
                'xp': int(row.xp),
            })
        if current_user_id is not None and row.user_id == current_user_id:
            current_user_block = {'rank': rank, 'xp': int(row.xp)}
    if current_user_id is not None and current_user_block is None:
        current_user_block = {'rank': None, 'xp': 0}
    return {'entries': entries, 'current_user': current_user_block}
