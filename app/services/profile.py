from app.models.volunteer import VolunteerProfile

def calculate_profile_completion(profile: VolunteerProfile | None) -> int:
    """
    Gerçek profil alanlarının doluluğuna göre %0-%100 arası profil tamamlanma oranı döner.
    Whitespace ('   '), null veya empty string olan alanlar 'boş' sayılır.
    Hesaplama, minimum profil gerekliliklerine (ad, soyad, şehir, bio, yetenekler, ilgi alanları) göre yapılır.
    """
    if not profile:
        return 0
        
    fields_string = [
        profile.first_name,
        profile.last_name,
        profile.city,
        profile.bio,
    ]
    
    filled = sum(1 for f in fields_string if f and f.strip())
    
    if len(profile.skills_list) > 0:
        filled += 1
    if len(profile.interests_list) > 0:
        filled += 1
        
    total_fields = 6
    return int((filled / total_fields) * 100)
