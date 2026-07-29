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
            dict(name='Türk Eğitim Vakfı (TEV)', description='Eğitimde fırsat eşitliği için öğrencilere burs ve eğitim destekleri sunan Türkiye\'nin köklü eğitim vakfı. TEV gönüllüsü olarak gençlerin aydınlık geleceğine katkı sağlayabilir, çeşitli projelerde mentor veya destekçi olarak yer alabilirsiniz.', website='https://www.tev.org.tr/bagis-ve-gonulluluk/gonullu-ol/tr', logo_url='https://www.google.com/s2/favicons?domain=tev.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='AKUT Arama Kurtarma Derneği', description='Doğal afetlerde, kazalarda arama kurtarma çalışmaları yapan, alanında öncü gönüllü kuruluş. AKUT gönüllüsü olarak arama kurtarma operasyonlarında, lojistik destekte veya farkındalık eğitimlerinde görev alabilirsiniz.', website='https://www.akut.org.tr/gonullu-olmak', logo_url='https://www.google.com/s2/favicons?domain=akut.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='TEMA Vakfı', description='Türkiye\'nin çöl olmasını engellemek, erozyonla mücadele ve doğa koruma çalışmaları yürüten vakıf. "Toprak Dede"nin izinden giderek fidan dikimi etkinliklerine, çevre eğitimlerine ve doğa yürüyüşlerine katılabilirsiniz.', website='https://www.tema.org.tr/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=tema.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Darüşşafaka Cemiyeti', description='Babası veya annesi hayatta olmayan, maddi olanakları yetersiz yetenekli çocuklara nitelikli eğitim veren cemiyet. Darüşşafaka\'nın eğitim misyonuna destek olmak için organizasyonlarda ve bağış kampanyalarında gönüllü olabilirsiniz.', website='https://www.darussafaka.org/gonullu-olun', logo_url='https://www.google.com/s2/favicons?domain=darussafaka.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türk Kızılay', description='Afet müdahalesi, kan hizmetleri ve insani yardımlar konusunda ulusal ve uluslararası ölçekte çalışan kurum. Kızılay gönüllüleri, kan bağışı organizasyonlarından afet bölgelerindeki yardım dağıtımlarına kadar geniş bir yelpazede çalışır.', website='https://gonulluol.org', logo_url='https://www.google.com/s2/favicons?domain=kizilay.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='LÖSEV', description='Lösemili çocukların sağlık ve eğitim başta olmak üzere her türlü ihtiyaçlarının sağlanması için çalışan vakıf. LSV Dükkan, hastane etkinlikleri veya kampanya süreçlerinde aktif rol alarak lösemili çocuklara umut olabilirsiniz.', website='https://www.losev.org.tr/v6/gonullu', logo_url='https://www.google.com/s2/favicons?domain=losev.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Hayvan Hakları Federasyonu (HAYTAP)', description='Hayvan haklarının yasalarla güvence altına alınması ve toplumda farkındalık yaratılması için çalışan federasyon. Barınak iyileştirme, mama dağıtımı ve hukuki hak arama süreçlerinde HAYTAP\'a destek olabilirsiniz.', website='https://www.haytap.org/tr/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=haytap.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Spastik Çocuklar Vakfı', description='Cerebral Palsy\'li çocuk ve erişkinlere teşhis, tedavi ve özel eğitim hizmeti veren vakıf. Etkinlik destekçisi, idari işler yardımcısı veya yetenekleriniz doğrultusunda özel atölye eğitmeni olarak çocuklara destek sağlayabilirsiniz.', website='https://www.tscv.org.tr/gonulluluk', logo_url='https://www.google.com/s2/favicons?domain=tscv.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='KAÇUV', description='Kanserli çocukların tedavilerinin sürekliliğini sağlamak ve ailelerine psikolojik, sosyal destek veren vakıf. Aile evlerinde, hastane oyun odalarında veya organizasyonlarda çocukların yüzünü güldüren etkinliklere katılabilirsiniz.', website='https://kacuv.org/gonullu-olun/', logo_url='https://www.google.com/s2/favicons?domain=kacuv.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Down Sendromu Derneği', description='Down sendromlu bireylerin toplumda bağımsız ve eşit yaşam sürmeleri için projeler üreten dernek. İş koçluğu, etkinlik asistanlığı veya farkındalık kampanyalarında görev alarak kapsayıcı bir toplum inşasına destek olabilirsiniz.', website='https://www.downturkiye.org/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=downturkiye.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Toplum Gönüllüleri Vakfı (TOG)', description='Gençlerin öncülüğünde sivil toplum projeleri yaratarak gençlerin kişisel gelişimlerini destekleyen vakıf. Üniversite kulüplerinde örgütlenerek yerel sorunlara çözüm üreten projeler tasarlayabilir ve uygulayabilirsiniz.', website='https://www.tog.org.tr/gonullu-ol/', logo_url='https://www.google.com/s2/favicons?domain=tog.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Kadın Emeğini Değerlendirme Vakfı (KEDV)', description='Dar gelirli kadınların ekonomik ve sosyal olarak güçlenmelerini, yerel kalkınmaya liderlik etmelerini destekleyen vakıf. Kadın kooperatifleri ve erken çocukluk eğitimi projelerinde uzmanlığınızla katkı sunabilirsiniz.', website='https://www.kedv.org.tr/bize-katilin', logo_url='https://www.google.com/s2/favicons?domain=kedv.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Korunmaya Muhtaç Çocuklar Vakfı (KORUNCUK)', description='Çocukların sevgi ve şefkatle büyüdüğü, eğitimlerinden mahrum kalmadığı bir yaşam kurmak için çalışan vakıf. Koruncukköy\'lerde veya idari ofislerde, çocukların sosyal ve kültürel gelişimlerine destek olabilirsiniz.', website='https://koruncuk.org/gonullu-ol/', logo_url='https://www.google.com/s2/favicons?domain=koruncuk.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='AÇEV', description='Erken çocukluk, anne-baba ve kadın destek eğitimleriyle toplumsal gelişime katkı sağlayan vakıf. Saha araştırmalarında, ofis çalışmalarında veya eğitim materyallerinin hazırlanmasında AÇEV ekibine gönüllü destek verebilirsiniz.', website='https://www.acev.org/gonullu-ol/', logo_url='https://www.google.com/s2/favicons?domain=acev.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Sakatlar Derneği', description='Engelli bireylerin haklarını savunan, onların sosyal ve ekonomik hayata entegrasyonu için çalışan dernek. Erişilebilirlik projeleri, tekerlekli sandalye dağıtımı ve sosyal etkinliklerde derneğin çalışmalarına destek olabilirsiniz.', website='https://www.tsd.org.tr/iletisim', logo_url='https://www.google.com/s2/favicons?domain=tsd.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Yeşilay', description='Toplumu başta sigara, alkol, uyuşturucu olmak üzere her türlü bağımlılıktan korumak için çalışan kurum. Sağlıklı yaşam bilincini artırmaya yönelik seminerler, gençlik kampları ve spor etkinliklerinde gönüllü elçi olabilirsiniz.', website='https://www.yesilay.org.tr/tr/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=yesilay.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türk Kanser Derneği', description='Kanser hastalıklarıyla ilgili farkındalık yaratma, erken teşhis ve tedavi süreçlerinde hastalara destek olan dernek. Bilinçlendirme kampanyalarında, hasta ziyaretlerinde veya organizasyonel süreçlerde yer alabilirsiniz.', website='https://www.turkkanserdernegi.org/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=turkkanserdernegi.org&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Mor Çatı Kadın Sığınağı Vakfı', description='Erkek şiddetine maruz kalan kadınlara psikolojik, hukuki destek veren ve sığınak çalışması yürüten vakıf. Dayanışma merkezlerinde, organizasyonlarda veya uzmanlık alanınıza (hukuk, psikoloji) göre gönüllü destek sağlayabilirsiniz.', website='https://morcati.org.tr/destek-olun/', logo_url='https://www.google.com/s2/favicons?domain=morcati.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='DenizTemiz Derneği (TURMEPA)', description='Türkiye\'nin denizlerinin ve su yollarının temizliğini sağlamak, korumak ve gelecek nesillere aktarmak için çalışan dernek. Kıyı temizlik etkinliklerine, sualtı atık çıkarma organizasyonlarına ve eğitim projelerine katılabilirsiniz.', website='https://www.turmepa.org.tr/gonullu-ol', logo_url='https://www.google.com/s2/favicons?domain=turmepa.org.tr&sz=128', phone='', address='', city='', is_verified=True),
            dict(name='Türkiye Tabiatını Koruma Derneği (TTKD)', description='Türkiye\'nin doğal zenginliklerini, flora ve faunasını korumak için bilimsel ve eğitimsel çalışmalar yapan dernek. Doğa kamplarında, ekolojik araştırmalarda ve çevre bilinci yaratma projelerinde aktif rol alabilirsiniz.', website='https://www.ttkd.org.tr/uyelik', logo_url='https://www.google.com/s2/favicons?domain=ttkd.org.tr&sz=128', phone='', address='', city='', is_verified=True),
        ]

        orgs = []
        for i, od in enumerate(orgs_data):
            o = Organization(user_id=org_users[i].id, **od)
            orgs.append(o)

        db.session.add_all(orgs)
        db.session.flush()

        print('[*] Etkinlikler olusturuluyor...')
        now = datetime.now(timezone.utc)

        events_data = [
            # Yeşil Gelecek (orgs[0])
            dict(organization_id=orgs[0].id, title='Sahil Temizleme Etkinliği',
                 description='İstanbul sahillerindeki plastik kirliliğini azaltmak için gerçekleştireceğimiz büyük temizlik etkinliğine davet ediliyorsunuz.',
                 category='çevre', city='İstanbul', address='Kadıköy Sahili',
                 start_date=now + timedelta(days=7), end_date=now + timedelta(days=7, hours=4),
                 max_volunteers=50, status='published', requirements='18 yaş ve üzeri.'),
            dict(organization_id=orgs[0].id, title='Fidan Dikme Kampanyası',
                 description="Belgrad Ormanı'nda 1000 fidan dikme kampanyasına katılın.",
                 category='çevre', city='İstanbul', address='Belgrad Ormanı, Sarıyer',
                 start_date=now + timedelta(days=14), end_date=now + timedelta(days=14, hours=6),
                 max_volunteers=100, status='published'),
            dict(organization_id=orgs[0].id, title='Sokak Hayvanları İçin Mama Dağıtımı',
                 description='Kış aylarında yiyecek bulmakta zorlanan sokak hayvanları için mama dağıtıyoruz.',
                 category='hayvan hakları', city='İstanbul', address='Beşiktaş',
                 start_date=now + timedelta(days=2), end_date=now + timedelta(days=2, hours=3),
                 max_volunteers=15, status='published'),
            # Umut Çocuk (orgs[1])
            dict(organization_id=orgs[1].id, title='Ücretsiz Matematik Dersi Gönüllüleri',
                 description='Dezavantajlı ilkokul öğrencilerine matematik dersi verecek gönüllü öğretmenler arıyoruz.',
                 category='eğitim', city='Ankara', address='Çankaya Kültür Merkezi',
                 start_date=now + timedelta(days=3), end_date=now + timedelta(days=3, hours=2),
                 max_volunteers=20, status='published', requirements='Matematik lisans öğrencisi.'),
            dict(organization_id=orgs[1].id, title='Yaz Kampı Aktivite Lideri',
                 description='Yaz kampımızda çocuklara eşlik edecek enerjik gönüllüler arıyoruz.',
                 category='çocuk', city='Ankara',
                 start_date=now + timedelta(days=30), end_date=now + timedelta(days=37),
                 max_volunteers=15, status='published'),
            dict(organization_id=orgs[1].id, title='Huzurevi Ziyareti ve Müzik Dinletisi',
                 description='Yaşlılarımıza moral vermek amacıyla düzenlenen müzik dinletisi ve sohbet.',
                 category='sosyal destek', city='Ankara', address='Çankaya Huzurevi',
                 start_date=now + timedelta(days=8), end_date=now + timedelta(days=8, hours=4),
                 max_volunteers=10, status='published'),
            dict(organization_id=orgs[1].id, title='Otizmli Çocuklar İçin Spor Şenliği',
                 description='Otizmli çocukların motor becerilerini geliştirmek için spor etkinlikleri.',
                 category='çocuk', city='Ankara', address='Yenimahalle Spor Kompleksi',
                 start_date=now + timedelta(days=18), end_date=now + timedelta(days=18, hours=6),
                 max_volunteers=30, status='published'),
            # Pati Dostları (orgs[2])
            dict(organization_id=orgs[2].id, title='Barınak Yenileme ve Boyama',
                 description='İzmir Bornova barınağının kışa hazırlık boyama ve tamirat işleri.',
                 category='hayvan hakları', city='İzmir', address='Bornova Barınağı',
                 start_date=now + timedelta(days=10), end_date=now + timedelta(days=10, hours=8),
                 max_volunteers=30, status='published'),
            dict(organization_id=orgs[2].id, title='Barınak Ziyareti ve Bakım',
                 description='Barınakta kalan hayvanlara sevgi ve bakım götürüyoruz.',
                 category='hayvan hakları', city='İzmir', address='Bornova Barınağı',
                 start_date=now + timedelta(days=5), end_date=now + timedelta(days=5, hours=3),
                 max_volunteers=20, status='published'),
            # Kodla Büyü (orgs[3])
            dict(organization_id=orgs[3].id, title='Hafta Sonu Python Atölyesi',
                 description='Lise öğrencilerine temel Python programlama eğitimi.',
                 category='eğitim', city='İstanbul', address='Şişli',
                 start_date=now + timedelta(days=5), end_date=now + timedelta(days=6, hours=4),
                 max_volunteers=10, status='published', requirements='Python bilgisi.'),
            dict(organization_id=orgs[3].id, title='Çocuklar İçin Temel Robotik Kodlama',
                 description='İlkokul çağındaki çocuklara robotik kodlamanın temellerini oyunlarla öğretiyoruz.',
                 category='eğitim', city='İstanbul', address='Şişli Gençlik Merkezi',
                 start_date=now + timedelta(days=20), end_date=now + timedelta(days=21),
                 max_volunteers=12, status='published', requirements='Temel kodlama bilgisi.'),
            # Deniz Temiz (orgs[4])
            dict(organization_id=orgs[4].id, title='Bodrum Sualtı Temizliği',
                 description='Dalış ekipmanıyla Bodrum koylarında sualtı çöp temizliği yapıyoruz.',
                 category='çevre', city='Muğla', address='Bodrum Merkezi İskele',
                 start_date=now + timedelta(days=12), end_date=now + timedelta(days=12, hours=5),
                 max_volunteers=25, status='published', requirements='Açık su dalış sertifikası.'),
            # Tohum ve Toprak (orgs[5])
            dict(organization_id=orgs[5].id, title='Kentsel Bahçe Kurulum Etkinliği',
                 description='Gaziantep\'in boş alanlarına topluluk bahçeleri kuruyoruz, toprağı birlikte işliyoruz.',
                 category='çevre', city='Gaziantep', address='Şehitkamil Parkı',
                 start_date=now + timedelta(days=9), end_date=now + timedelta(days=9, hours=6),
                 max_volunteers=40, status='published'),
            # Yaşlı Dostu İzmir (orgs[6])
            dict(organization_id=orgs[6].id, title='Yaşlı Ziyareti ve Sohbet Gönüllüsü',
                 description='Yalnız yaşayan yaşlı bireylerin evlerini ziyaret ederek moral kaynağı oluyoruz.',
                 category='sosyal destek', city='İzmir', address='Konak',
                 start_date=now + timedelta(days=4), end_date=now + timedelta(days=4, hours=3),
                 max_volunteers=20, status='published'),
            # Genç Liderler Ağı (orgs[7])
            dict(organization_id=orgs[7].id, title='Gençlik Liderlik Kampı',
                 description='18-25 yaş gençlerin sivil toplum liderliği konusunda beceri geliştireceği haftalık kamp.',
                 category='eğitim', city='Ankara', address='Bolu Ormanları',
                 start_date=now + timedelta(days=25), end_date=now + timedelta(days=32),
                 max_volunteers=30, status='published'),
            # Bursa Afet Gönüllüleri (orgs[8])
            dict(organization_id=orgs[8].id, title='Afet Hazırlık ve İlk Yardım Eğitimi',
                 description='Deprem ve sel senaryolarında ilk yardım ve toplanma noktası uygulamaları.',
                 category='afet yardımı', city='Bursa', address='Osmangazi Toplantı Salonu',
                 start_date=now + timedelta(days=6), end_date=now + timedelta(days=6, hours=8),
                 max_volunteers=50, status='published'),
            # Mülteci Dayanışma (orgs[9])
            dict(organization_id=orgs[9].id, title='Türkçe Dil Sınıfı Gönüllü Öğretmeni',
                 description='İstanbul\'daki mülteci ve göçmenlere temel Türkçe öğretecek gönüllü öğretmenler arıyoruz.',
                 category='eğitim', city='İstanbul', address='Fatih Kültür Merkezi',
                 start_date=now + timedelta(days=3), end_date=now + timedelta(days=3, hours=3),
                 max_volunteers=15, status='published'),
            # Kültür ve Sanat Köprüsü (orgs[10])
            dict(organization_id=orgs[10].id, title='Çocuk Tiyatro Atölyesi',
                 description='7-14 yaş çocuklara tiyatro, drama ve sahne sanatları eğitimi.',
                 category='kültür sanat', city='Eskişehir', address='Odunpazarı Kültür Evi',
                 start_date=now + timedelta(days=11), end_date=now + timedelta(days=11, hours=4),
                 max_volunteers=10, status='published'),
            # Sağlıklı Toplum (orgs[11])
            dict(organization_id=orgs[11].id, title='Kırsal Sağlık Taraması Seferberliği',
                 description='Gaziantep köylerinde ücretsiz kan tahlili, tansiyon ve şeker ölçüm taraması.',
                 category='sağlık', city='Gaziantep', address='Şahinbey İlçe Merkezi',
                 start_date=now + timedelta(days=15), end_date=now + timedelta(days=15, hours=6),
                 max_volunteers=20, status='published', requirements='Tıp, hemşirelik veya eczacılık öğrencisi olmak.'),
            # Tarih ve Bellek (orgs[12])
            dict(organization_id=orgs[12].id, title='Şehir Tarihi Belgeleme Yürüyüşü',
                 description='Trabzon\'un tarihi alanlarını fotoğraflayarak dijital arşiv oluşturuyoruz.',
                 category='kültür sanat', city='Trabzon', address='Ortahisar Kalesi Çevresi',
                 start_date=now + timedelta(days=13), end_date=now + timedelta(days=13, hours=4),
                 max_volunteers=15, status='published'),
            # Engelsiz Erişim (orgs[13])
            dict(organization_id=orgs[13].id, title='Görme Engelliler İçin Sesli Kitap Okuma',
                 description='Görme engelli bireyler için klasik eserleri seslendireceğiz, gönüllü seslendirici arıyoruz.',
                 category='sosyal destek', city='Ankara', address='Mamak Kültür Evi',
                 start_date=now + timedelta(days=7), end_date=now + timedelta(days=7, hours=3),
                 max_volunteers=12, status='published'),
            # İklim Gençlik (orgs[14])
            dict(organization_id=orgs[14].id, title='Okullarda İklim Bilinci Atölyesi',
                 description='İlk ve ortaokullarda iklim değişikliği farkındalığı için interaktif atölyeler düzenliyoruz.',
                 category='çevre', city='İstanbul', address='Beşiktaş Anadolu Lisesi',
                 start_date=now + timedelta(days=6), end_date=now + timedelta(days=6, hours=2),
                 max_volunteers=8, status='published'),
            dict(organization_id=orgs[14].id, title='Orman Yangınlarını Önleme Eğitimi',
                 description='Yaz ayları öncesi orman yangınlarına karşı alınabilecek önlemler hakkında bilinçlendirme.',
                 category='çevre', city='Muğla', address='Marmaris Orman Bölge Müdürlüğü',
                 start_date=now + timedelta(days=40), end_date=now + timedelta(days=41),
                 max_volunteers=50, status='published'),
        ]

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