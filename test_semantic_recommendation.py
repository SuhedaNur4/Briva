import os
from app import create_app, db
from app.models.volunteer import VolunteerProfile
from app.models.event import Event
from app.models.application import EventApplication
from app.recommend import UserContext, RecommendationEngine, cosine_similarity
from app.utils.ai_analyzer import get_embedding
from dotenv import load_dotenv

load_dotenv()

app = create_app()
app.app_context().push()

# Find a volunteer who has a non-empty profile
profiles = VolunteerProfile.query.all()
test_profile = None
for p in profiles:
    if p.skills_list or p.interests_list:
        test_profile = p
        break

if not test_profile:
    print("Test için uygun gönüllü profili bulunamadı.")
    exit(0)

print(f"### REAL TEST RESULT\n")
print(f"Gerçek kullanıcı ID: {test_profile.user_id}")
print(f"DB İlgi Alanları: {test_profile.interests_list}")
print(f"DB Becerileri: {test_profile.skills_list}")
print(f"DB Şehir: {test_profile.city}")

user_context = UserContext.from_volunteer_profile(test_profile)

applications = EventApplication.query.filter_by(user_id=test_profile.user_id).all()
past_apps = []
past_parts = []
for app_model in applications:
    if app_model.event and app_model.event.title:
        if app_model.status == 'completed':
            past_parts.append(app_model.event.title)
        else:
            past_apps.append(app_model.event.title)

user_context.past_applications = past_apps
user_context.past_participations = past_parts

print(f"\nUserContext:\nCity: {user_context.city}\nInterests: {user_context.interests}\nSkills: {user_context.skills}\nPast Apps: {user_context.past_applications}\nPast Parts: {user_context.past_participations}")

context_text = user_context.get_context_text()
print(f"\nEmbedding Context Text: {context_text}\n")

events = Event.query.filter_by(status='published').all()
engine = RecommendationEngine(threshold=0, max_results=5)

def print_recommendations(u_context, title):
    u_emb = get_embedding(u_context.get_context_text())
    print(f"### {title}")
    print(f"{'Etkinlik':<35} | {'Rule Score':<10} | {'Cosine':<8} | {'Sem Bonus':<9} | Final Score")
    print("-" * 80)

    recs = engine.recommend(u_context, events)
    for r in recs[:5]:
        sim = 0.0
        sb = r.breakdown.get('semantic_similarity', 0)
        e_emb = engine._get_event_embedding(Event.query.get(r.event_id))
        if u_emb and e_emb:
            sim = cosine_similarity(u_emb, e_emb)
        rs = sum(v for k, v in r.breakdown.items() if k != 'semantic_similarity' and isinstance(v, int))
        print(f"{r.event_title[:35]:<35} | {rs:<10} | {sim:.4f}   | {sb:<9} | {r.total_score}")
    print("\n")

print_recommendations(user_context, "TOP 5 RECOMMENDATIONS (GERÇEK VERİ)")

# Senaryo A
context_a = UserContext(
    interests=['eğitim', 'kodlama', 'çocuklarla çalışma'],
    skills=['kodlama', 'öğretmenlik']
)
print_recommendations(context_a, "SCENARIO A (Eğitim, Kodlama, Çocuklar)")

# Senaryo B
context_b = UserContext(
    interests=['hayvan hakları', 'hayvan bakımı', 'sosyal sorumluluk'],
    skills=['hayvan bakımı', 'iletişim']
)
print_recommendations(context_b, "SCENARIO B (Hayvan hakları, Hayvan bakımı)")
