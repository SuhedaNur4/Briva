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

        # 15 STK kullanıcısı
        org_users = []
        for i in range(1, 21):
            u = User(email=f'stk{i}@briva.com', role='organization')
            u.set_password('password123')
            org_users.append(u)

        admin = User(email='admin@briva.com', role='admin')
        admin.set_password('admin123456')

        db.session.add_all([volunteer1, volunteer2, volunteer3] + org_users + [admin])
        db.session.flush()

        print('[*] Gonullu profilleri olusturuluyor...')
        profile1 = VolunteerProfile(user_id=volunteer1.id, first_name='Ali', last_name='Yılmaz',
            phone='0532 111 22 33', birth_date=date(1995, 3, 15), city='İstanbul',
            bio='Çevre ve eğitim alanında gönüllü çalışmalar yapmak istiyorum.',
            interests='çevre,eğitim,teknoloji', skills='Python,İngilizce,iletişim')
        profile2 = VolunteerProfile(user_id=volunteer2.id, first_name='Ayşe', last_name='Kaya',
            phone='0533 444 55 66', birth_date=date(1998, 7, 22), city='Ankara',
            bio='Sağlık ve sosyal yardım projelerinde aktif olmak istiyorum.',
            interests='sağlık,sosyal destek,çocuk', skills='hemşirelik,ilk yardım,Fransızca')
        profile3 = VolunteerProfile(user_id=volunteer3.id, first_name='Mehmet', last_name='Demir',
            city='İzmir', interests='hayvan hakları,çevre', skills='fotoğrafçılık,sosyal medya')
        db.session.add_all([profile1, profile2, profile3])

        print('[*] 15 STK profili olusturuluyor...')
        orgs_data = [
            dict(name='Türk Eğitim Vakfı (TEV)', description='Eğitimde fırsat eşitliği için öğrencilere burs ve eğitim destekleri sunan Türkiye\'nin köklü eğitim vakfı. TEV gönüllüsü olarak gençlerin aydınlık geleceğine katkı sağlayabilir, çeşitli projelerde mentor veya destekçi olarak yer alabilirsiniz.', website='https://www.tev.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=tev.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='AKUT Arama Kurtarma Derneği', description='Doğal afetlerde, kazalarda arama kurtarma çalışmaları yapan, alanında öncü gönüllü kuruluş. AKUT gönüllüsü olarak arama kurtarma operasyonlarında, lojistik destekte veya farkındalık eğitimlerinde görev alabilirsiniz.', website='https://www.akut.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=akut.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='TEMA Vakfı', description='Türkiye\'nin çöl olmasını engellemek, erozyonla mücadele ve doğa koruma çalışmaları yürüten vakıf. "Toprak Dede"nin izinden giderek fidan dikimi etkinliklerine, çevre eğitimlerine ve doğa yürüyüşlerine katılabilirsiniz.', website='https://www.tema.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=tema.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Darüşşafaka Cemiyeti', description='Babası veya annesi hayatta olmayan, maddi olanakları yetersiz yetenekli çocuklara nitelikli eğitim veren cemiyet. Darüşşafaka\'nın eğitim misyonuna destek olmak için organizasyonlarda ve bağış kampanyalarında gönüllü olabilirsiniz.', website='https://www.darussafaka.org/', logo_url='https://www.google.com/s2/favicons?domain=darussafaka.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türk Kızılay', description='Afet müdahalesi, kan hizmetleri ve insani yardımlar konusunda ulusal ve uluslararası ölçekte çalışan kurum. Kızılay gönüllüleri, kan bağışı organizasyonlarından afet bölgelerindeki yardım dağıtımlarına kadar geniş bir yelpazede çalışır.', website='https://www.kizilay.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=kizilay.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='LÖSEV', description='Lösemili çocukların sağlık ve eğitim başta olmak üzere her türlü ihtiyaçlarının sağlanması için çalışan vakıf. LSV Dükkan, hastane etkinlikleri veya kampanya süreçlerinde aktif rol alarak lösemili çocuklara umut olabilirsiniz.', website='https://www.losev.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=losev.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Hayvan Hakları Federasyonu (HAYTAP)', description='Hayvan haklarının yasalarla güvence altına alınması ve toplumda farkındalık yaratılması için çalışan federasyon. Barınak iyileştirme, mama dağıtımı ve hukuki hak arama süreçlerinde HAYTAP\'a destek olabilirsiniz.', website='https://www.haytap.org/', logo_url='https://www.google.com/s2/favicons?domain=haytap.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Spastik Çocuklar Vakfı', description='Cerebral Palsy\'li çocuk ve erişkinlere teşhis, tedavi ve özel eğitim hizmeti veren vakıf. Etkinlik destekçisi, idari işler yardımcısı veya yetenekleriniz doğrultusunda özel atölye eğitmeni olarak çocuklara destek sağlayabilirsiniz.', website='https://www.tscv.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=tscv.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='KAÇUV', description='Kanserli çocukların tedavilerinin sürekliliğini sağlamak ve ailelerine psikolojik, sosyal destek veren vakıf. Aile evlerinde, hastane oyun odalarında veya organizasyonlarda çocukların yüzünü güldüren etkinliklere katılabilirsiniz.', website='https://kacuv.org/', logo_url='https://www.google.com/s2/favicons?domain=kacuv.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Down Sendromu Derneği', description='Down sendromlu bireylerin toplumda bağımsız ve eşit yaşam sürmeleri için projeler üreten dernek. İş koçluğu, etkinlik asistanlığı veya farkındalık kampanyalarında görev alarak kapsayıcı bir toplum inşasına destek olabilirsiniz.', website='https://www.downturkiye.org/', logo_url='https://www.google.com/s2/favicons?domain=downturkiye.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Toplum Gönüllüleri Vakfı (TOG)', description='Gençlerin öncülüğünde sivil toplum projeleri yaratarak gençlerin kişisel gelişimlerini destekleyen vakıf. Üniversite kulüplerinde örgütlenerek yerel sorunlara çözüm üreten projeler tasarlayabilir ve uygulayabilirsiniz.', website='https://www.tog.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=tog.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Kadın Emeğini Değerlendirme Vakfı (KEDV)', description='Dar gelirli kadınların ekonomik ve sosyal olarak güçlenmelerini, yerel kalkınmaya liderlik etmelerini destekleyen vakıf. Kadın kooperatifleri ve erken çocukluk eğitimi projelerinde uzmanlığınızla katkı sunabilirsiniz.', website='https://www.kedv.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=kedv.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Korunmaya Muhtaç Çocuklar Vakfı (KORUNCUK)', description='Çocukların sevgi ve şefkatle büyüdüğü, eğitimlerinden mahrum kalmadığı bir yaşam kurmak için çalışan vakıf. Koruncukköy\'lerde veya idari ofislerde, çocukların sosyal ve kültürel gelişimlerine destek olabilirsiniz.', website='https://koruncuk.org/', logo_url='https://www.google.com/s2/favicons?domain=koruncuk.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='AÇEV', description='Erken çocukluk, anne-baba ve kadın destek eğitimleriyle toplumsal gelişime katkı sağlayan vakıf. Saha araştırmalarında, ofis çalışmalarında veya eğitim materyallerinin hazırlanmasında AÇEV ekibine gönüllü destek verebilirsiniz.', website='https://www.acev.org/', logo_url='https://www.google.com/s2/favicons?domain=acev.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Sakatlar Derneği', description='Engelli bireylerin haklarını savunan, onların sosyal ve ekonomik hayata entegrasyonu için çalışan dernek. Erişilebilirlik projeleri, tekerlekli sandalye dağıtımı ve sosyal etkinliklerde derneğin çalışmalarına destek olabilirsiniz.', website='https://www.tsd.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=tsd.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Yeşilay', description='Toplumu başta sigara, alkol, uyuşturucu olmak üzere her türlü bağımlılıktan korumak için çalışan kurum. Sağlıklı yaşam bilincini artırmaya yönelik seminerler, gençlik kampları ve spor etkinliklerinde gönüllü elçi olabilirsiniz.', website='https://www.yesilay.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=yesilay.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türk Kanser Derneği', description='Kanser hastalıklarıyla ilgili farkındalık yaratma, erken teşhis ve tedavi süreçlerinde hastalara destek olan dernek. Bilinçlendirme kampanyalarında, hasta ziyaretlerinde veya organizasyonel süreçlerde yer alabilirsiniz.', website='https://www.turkkanserdernegi.org/', logo_url='https://www.google.com/s2/favicons?domain=turkkanserdernegi.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Mor Çatı Kadın Sığınağı Vakfı', description='Erkek şiddetine maruz kalan kadınlara psikolojik, hukuki destek veren ve sığınak çalışması yürüten vakıf. Dayanışma merkezlerinde, organizasyonlarda veya uzmanlık alanınıza (hukuk, psikoloji) göre gönüllü destek sağlayabilirsiniz.', website='https://morcati.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=morcati.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='DenizTemiz Derneği (TURMEPA)', description='Türkiye\'nin denizlerinin ve su yollarının temizliğini sağlamak, korumak ve gelecek nesillere aktarmak için çalışan dernek. Kıyı temizlik etkinliklerine, sualtı atık çıkarma organizasyonlarına ve eğitim projelerine katılabilirsiniz.', website='https://www.turmepa.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=turmepa.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Tabiatını Koruma Derneği (TTKD)', description='Türkiye\'nin doğal zenginliklerini, flora ve faunasını korumak için bilimsel ve eğitimsel çalışmalar yapan dernek. Doğa kamplarında, ekolojik araştırmalarda ve çevre bilinci yaratma projelerinde aktif rol alabilirsiniz.', website='https://www.ttkd.org.tr/', logo_url='https://www.google.com/s2/favicons?domain=ttkd.org.tr&sz=128', phone='', address='', city='', is_verified=True),
        ]

        orgs = []
        for i, od in enumerate(orgs_data):
            o = Organization(user_id=org_users[i].id, **od)
            orgs.append(o)

        db.session.add_all(orgs)
        db.session.flush()

        print('[*] Etkinlikler olusturuluyor...')
        now = datetime.now(timezone.utc)

        events_data = []
        categories = ['çevre', 'eğitim', 'sosyal destek', 'hayvan hakları', 'sağlık', 'kültür sanat', 'afet yardımı']
        cities = ['İstanbul', 'Ankara', 'İzmir', 'Gaziantep', 'Bursa', 'Antalya', 'Trabzon']
        
        for i, org in enumerate(orgs):
            # Etkinlik 1
            events_data.append(dict(
                organization_id=org.id,
                title=f'{org.name} - Saha Çalışması ve Destek',
                description=f'{org.name} misyonuna katkı sağlamak üzere sahada aktif görev alacak enerjik gönüllüler arıyoruz. Etkinlik boyunca lojistik ve organizasyon süreçlerine destek vereceksiniz.',
                category=categories[i % len(categories)],
                city=cities[i % len(cities)],
                address='Şehir Merkezi Proje Alanı',
                start_date=now + timedelta(days=i+2),
                end_date=now + timedelta(days=i+2, hours=5),
                max_volunteers=25,
                status='published',
                requirements='18 yaş üzeri, iletişim becerisi kuvvetli.'
            ))
            # Etkinlik 2
            events_data.append(dict(
                organization_id=org.id,
                title=f'{org.name} - Farkındalık ve Eğitim Atölyesi',
                description=f'{org.name} projelerinin topluma duyurulması ve eğitici atölyelerde asistanlık yapmak üzere gönüllüler aranıyor.',
                category='eğitim',
                city='Online',
                address='Uzaktan Katılım',
                start_date=now + timedelta(days=i+5),
                end_date=now + timedelta(days=i+12),
                max_volunteers=15,
                status='published'
            ))

        events = []
        for ed in events_data:
            e = Event(**ed)
            events.append(e)

        db.session.add_all(events)
        db.session.flush()

        print('[*] Basvurular olusturuluyor...')
        app1 = EventApplication(user_id=volunteer1.id, event_id=events[0].id, status='approved',
            cover_letter='Çevre konusunda duyarlıyım.', reviewer_note='Onaylandı!')
        app2 = EventApplication(user_id=volunteer2.id, event_id=events[3].id, status='pending',
            cover_letter='Matematik öğretmenliği mezunuyum.')
        app3 = EventApplication(user_id=volunteer1.id, event_id=events[3].id, status='pending',
            cover_letter='Üniversitede matematik okuyorum.')
        app4 = EventApplication(user_id=volunteer3.id, event_id=events[0].id, status='pending',
            cover_letter='Sahil temizliğine katkıda bulunmak istiyorum.')
        app5 = EventApplication(user_id=volunteer3.id, event_id=events[7].id, status='approved',
            cover_letter='Hayvanları çok seviyorum.', reviewer_note='Bekliyoruz!')
        app6 = EventApplication(user_id=volunteer1.id, event_id=events[9].id, status='pending',
            cover_letter='Python geliştiricisiyim.')
        db.session.add_all([app1, app2, app3, app4, app5, app6])
        db.session.commit()

        print('\n[OK] Seed tamamlandi!\n')
        print('=' * 50)
        print('Test kullanicilari (parola: password123):')
        print('  Gonullu 1 : ali@example.com')
        print('  Gonullu 2 : ayse@example.com')
        print('  Gonullu 3 : mehmet@example.com')
        for i in range(1, 21):
            print(f'  STK {i:<2}    : stk{i}@briva.com')
        print('  Admin     : admin@briva.com (parola: admin123456)')
        print('=' * 50)
        print(f'  Organizasyonlar: {Organization.query.count()} adet')
        print(f'  Etkinlikler    : {Event.query.count()} adet')
        print(f'  Basvurular     : {EventApplication.query.count()} adet')
        print('=' * 50)

if __name__ == '__main__':
    seed()
