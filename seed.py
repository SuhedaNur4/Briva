import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import datetime, date, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.volunteer import VolunteerProfile
from app.models.organization import Organization
from app.models.event import Event
from app.models.application import EventApplication

def seed():
    app = create_app()
    with app.app_context():
        print('[*] Mevcut veriler temizleniyor...')
        EventApplication.query.delete()
        Event.query.delete()
        Organization.query.delete()
        VolunteerProfile.query.delete()
        User.query.delete()
        db.session.commit()
        print('[*] Kullaniciler olusturuluyor...')
        volunteer1 = User(email='ali@example.com', role='volunteer')
        volunteer1.set_password('password123')
        volunteer2 = User(email='ayse@example.com', role='volunteer')
        volunteer2.set_password('password123')
        volunteer3 = User(email='mehmet@example.com', role='volunteer')
        volunteer3.set_password('password123')
        org_user1 = User(email='stk1@briva.com', role='organization')
        org_user1.set_password('password123')
        org_user2 = User(email='stk2@briva.com', role='organization')
        org_user2.set_password('password123')
        admin = User(email='admin@briva.com', role='admin')
        admin.set_password('admin123456')
        db.session.add_all([volunteer1, volunteer2, volunteer3, org_user1, org_user2, admin])
        db.session.flush()
        print('[*] Gonullu profilleri olusturuluyor...')
        profile1 = VolunteerProfile(user_id=volunteer1.id, first_name='Ali', last_name='Yılmaz', phone='0532 111 22 33', birth_date=date(1995, 3, 15), city='İstanbul', bio='Çevre ve eğitim alanında gönüllü çalışmalar yapmak istiyorum.', interests='çevre,eğitim,teknoloji', skills='Python,İngilizce,iletişim')
        profile2 = VolunteerProfile(user_id=volunteer2.id, first_name='Ayşe', last_name='Kaya', phone='0533 444 55 66', birth_date=date(1998, 7, 22), city='Ankara', bio='Sağlık ve sosyal yardım projelerinde aktif olmak istiyorum.', interests='sağlık,sosyal yardım,çocuk', skills='hemşirelik,ilk yardım,Fransızca')
        profile3 = VolunteerProfile(user_id=volunteer3.id, first_name='Mehmet', last_name='Demir', city='İzmir', interests='hayvan hakları,çevre', skills='fotoğrafçılık,sosyal medya')
        db.session.add_all([profile1, profile2, profile3])
        print('[*] STK profilleri olusturuluyor...')
        org1 = Organization(user_id=org_user1.id, name='Yeşil Gelecek Derneği', description='Çevre koruma ve sürdürülebilirlik alanında faaliyet gösteren sivil toplum kuruluşu.', website='https://yesilgelecek.org', phone='0212 555 11 22', address='Kadıköy, İstanbul', city='İstanbul', is_verified=True)
        org2 = Organization(user_id=org_user2.id, name='Umut Çocuk Vakfı', description='Dezavantajlı çocuklara eğitim ve sosyal destek sağlayan vakıf.', website='https://umutcocuk.org', phone='0312 444 77 88', address='Çankaya, Ankara', city='Ankara', is_verified=True)
        db.session.add_all([org1, org2])
        db.session.flush()
        print('[*] Etkinlikler olusturuluyor...')
        now = datetime.now(timezone.utc)
        event1 = Event(organization_id=org1.id, title='Sahil Temizleme Etkinliği', description='İstanbul sahillerindeki plastik kirliliğini azaltmak için gerçekleştireceğimiz büyük temizlik etkinliğine davet ediliyorsunuz. Eldiven ve poşetler tarafımızca sağlanacaktır.', category='çevre', city='İstanbul', address='Kadıköy Sahili, İstanbul', start_date=now + timedelta(days=7), end_date=now + timedelta(days=7, hours=4), max_volunteers=50, status='published', requirements='Fiziksel olarak aktif olabilmek. 18 yaş ve üzeri.')
        event2 = Event(organization_id=org1.id, title='Fidan Dikme Kampanyası', description="Belgrad Ormanı'nda 1000 fidan dikme kampanyasına katılın. Gönüllülerimizle birlikte geleceğe yeşil bir dokunuş bırakıyoruz.", category='çevre', city='İstanbul', address='Belgrad Ormanı, Sarıyer', start_date=now + timedelta(days=14), end_date=now + timedelta(days=14, hours=6), max_volunteers=100, status='published')
        event3 = Event(organization_id=org2.id, title='Ücretsiz Matematik Dersi Gönüllüleri', description="Ankara'daki dezavantajlı ilkokul öğrencilerine matematik dersi verecek gönüllü öğretmenler arıyoruz. Haftada 2 saat yeterlidir.", category='eğitim', city='Ankara', address='Çankaya Kültür Merkezi, Ankara', start_date=now + timedelta(days=3), end_date=now + timedelta(days=3, hours=2), max_volunteers=20, status='published', requirements='Matematik lisans öğrencisi veya mezunu olmak.')
        event4 = Event(organization_id=org2.id, title='Yaz Kampı Aktivite Lideri', description='Yaz kampımızda çocuklara eşlik edecek enerjik gönüllüler arıyoruz.', category='çocuk', city='Ankara', start_date=now + timedelta(days=30), end_date=now + timedelta(days=37), max_volunteers=15, status='published')
        db.session.add_all([event1, event2, event3, event4])
        db.session.flush()
        print('[*] Basvurular olusturuluyor...')
        app1 = EventApplication(user_id=volunteer1.id, event_id=event1.id, status='approved', cover_letter='Çevre konusunda duyarlıyım ve bu etkinliğe katılmak istiyorum.', reviewer_note='Başvurunuz onaylandı. Sizi aramızda görmekten mutluluk duyarız!')
        app2 = EventApplication(user_id=volunteer2.id, event_id=event3.id, status='pending', cover_letter='Matematik öğretmenliği mezunuyum, destek olmak isterim.')
        app3 = EventApplication(user_id=volunteer1.id, event_id=event3.id, status='pending', cover_letter='Üniversitede matematik okuyorum. Haftasonları uygunum.')
        app4 = EventApplication(user_id=volunteer3.id, event_id=event1.id, status='pending', cover_letter='Sahil temizliğine katkıda bulunmak istiyorum.')
        db.session.add_all([app1, app2, app3, app4])
        db.session.commit()
        print('\n[OK] Seed tamamlandi!\n')
        print('=' * 50)
        print('Test kullanicilari (parola: password123):')
        print('  Gonullu 1 : ali@example.com')
        print('  Gonullu 2 : ayse@example.com')
        print('  Gonullu 3 : mehmet@example.com')
        print('  STK 1     : stk1@briva.com')
        print('  STK 2     : stk2@briva.com')
        print('  Admin     : admin@briva.com (parola: admin123456)')
        print('=' * 50)
        print(f'  Etkinlikler: {Event.query.count()} adet')
        print(f'  Başvurular : {EventApplication.query.count()} adet')
        print('=' * 50)
if __name__ == '__main__':
    seed()