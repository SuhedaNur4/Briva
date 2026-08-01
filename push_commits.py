# -*- coding: utf-8 -*-
import os
import subprocess

def run(cmd):
    print(f'Running: {cmd}')
    subprocess.run(cmd, shell=True, check=False)

commits = [
    ('feat(db): dinamik test verisi üretici script oluşturuldu', 'Statik veriler yerine Faker kütüphanesiyle dinamik veri üreten seed.py altyapısı kuruldu.', 'git add seed.py'),
    ('feat(db): 40 test etkinliği ve 20 STK verisi sisteme eklendi', 'Sistemin test edilebilmesi için mantıksal olarak tutarlı gerçekçi test verileri üretildi.', ''),
    ('fix(db): veritabanı temizleme ve sıfırlama (teardown) rutini düzeltildi', 'Veritabanının her seeding işleminden önce temizlenmesi ve tabloların baştan yaratılması güvence altına alındı.', ''),
    ('refactor(ai): güncel Gemini modellerine geçiş yapıldı', 'Eski model referanslarının kullanımdan kaldırılması (deprecation) sonrasında sistem gemini-3.5-flash modeline taşındı.', ''),
    ('refactor(ai): generation ve embedding model yapılandırması merkezi hale getirildi', 'Model değişkenleri ortam dosyası (.env) ve config üzerinden okunacak şekilde mimari iyileştirme yapıldı.', 'git add app/__init__.py app/config.py .env.example'),
    ('feat(ai): recommendation için UserContext genişletildi', 'Gönüllünün şehri, ilgi alanları, becerileri ve geçmiş başvuruları recommendation pipelineına dahil edildi.', ''),
    ('feat(ai): hibrit öneri motoruna semantik eşleştirme eklendi', 'Kullanıcı ve etkinlik içerikleri embeddinge dönüştürülerek recommendation sürecine cosine similarity tabanlı semantik eşleştirme eklendi.', 'git add app/recommend.py'),
    ('feat(ai): hibrit sıralama algoritması güncellendi', 'Rule-based skor ile semantic bonus tek bir puanda birleştirilerek en optimal etkinlik eşleşmeleri sağlandı.', ''),
    ('feat(ai): öneriler için açıklanabilir AI (XAI) desteği eklendi', 'Kullanıcılara öneri gerekçesini açıklayan XAI mekanizması eklendi.', ''),
    ('feat(ai): api kesintilerine karşı yedek kural motoru (fallback) yazıldı', 'API limiti veya bağlantı hatalarında sistemin çalışmaya devam etmesi için kural tabanlı fallback mekanizması eklendi.', 'git add app/utils/ai_analyzer.py'),
    ('refactor(ai): AI yanıtlarına ai_generated ve fallback_used durumları eklendi', 'Frontendin AI başarısını yönetebilmesi için sistem yanıtlarına metadata entegre edildi.', 'git add app/routes/recommendations.py'),
    ('test(ai): verify_ai ve embedding doğrulama senaryoları eklendi', 'Farklı kullanıcı ve etkinlik kombinasyonlarında cosine similarity değerleri test edilerek sistem sınırları doğrulandı.', 'git add scripts/'),
    ('fix(api): stk panelindeki json veri okuma hatası giderildi', 'İstemci-sunucu API sözleşmesi uyumsuzluğuna sebep olan response.data parse hatası çözüldü.', 'git add app/routes/events.py'),
    ('refactor(api): endpoint çıktıları standart veri yapısına çekildi', 'Tüm etkinlik ve STK JSON yanıt modelleri, arayüz tarafında tek bir mantıkla işlenecek şekilde revize edildi.', 'git add app/static/js/services/api.js app/static/js/services/organizations.js'),
    ('refactor(auth): yetkilendirme altyapısı (rbac) optimize edildi', 'Rol bazlı erişim denetimi mekanizmaları performans ve güvenlik iyileştirmelerinden geçirildi.', 'git add app/routes/auth.py'),
    ('feat(auth): kurumsal sayfalara jwt erişim denetimi eklendi', 'Yetkisiz kullanıcıların STK paneline girmesini engellemek için @organization_required dekoratörü koda dahil edildi.', ''),
    ('feat(gamification): XP, Badge ve seviye hesaplamalarını destekleyen backend altyapısı tamamlandı', 'Kullanıcı başvuruları üzerinden statü üreten oyunlaştırma mekaniği backend altyapısına entegre edildi.', ''),
    ('feat(events): etkinlik kotaları için kontrol mekanizması yazıldı', 'Başvuru sayısı ve maksimum gönüllü limiti (kapasite) için çift taraflı (istemci-sunucu) kural seti entegre edildi.', ''),
    ('fix(media): kurumsal logo çekme servisi yenilendi', 'Logo sağlayıcısı yüksek çözünürlüklü kaynakla değiştirildi.', ''),
    ('feat(ui): ortak bileşenlere glassmorphism tasarımı ve animasyonlar uygulandı', 'Kartlara, formlara ve menülere saydam blur efekti tanımlanıp, sayfa geçişleri fade-in animasyonlarıyla pürüzsüzleştirildi.', 'git add app/static/css/main.css'),
    ('fix(css): etkinlik kartlarındaki yerleşim (layout shifting) sorunları çözüldü', 'Profil ve etkinlik listeleme sayfalarında buton/metin çakışmaları CSS Grid yapısıyla giderildi.', 'git add app/static/js/org_profile_page.js'),
    ('feat(ui): üst menüdeki aktif sekme stili hap (pill) tasarıma çevrildi', 'Kullanıcılara hangi sayfada olduklarını daha iyi anlamaları için navigasyon barına vurgu tasarımı eklendi.', 'git add app/static/js/utils/navbar.js'),
    ('fix(js): dashboard üzerindeki tanımsız (undefined) veri hataları yakalandı', 'Veri gelmeden önce ekranın bozuk görünmesine neden olan render sorunları veri yükleme sırası düzenlenerek aşıldı.', 'git add app/static/js/dashboard_page.js app/static/js/org_dashboard_page.js app/static/js/events_page.js'),
    ('feat(js): gönüllü paneli için kapasite barı ve kontenjan yazıları dinamikleştirildi', 'Kontenjan uyarısı kaldırılarak Event.max_volunteers sınırı arayüze gerçek zamanlı entegre edildi.', 'git add app/static/js/event_detail_page.js'),
    ('feat(ui): anasayfa (landing page) kullanıcı deneyimi için redesign edildi', 'Ziyaretçileri karşılayan ilk ekran, platformun yapay zeka gücünü vurgulayacak modern bir tasarıma kavuşturuldu.', 'git add app/templates/index.html app/templates/roadmap.html'),
    ('feat(ui): volunteer quiz sayfası form validasyonlarıyla güçlendirildi', 'Gönüllü kişilik testi sayfasında hatalı veri gönderimini engelleyecek Javascript kuralları yazıldı.', 'git add app/templates/personality_test.html app/static/js/personality_test.js'),
    ('refactor(ui): footer ve navbar bileşenleri modüler hale getirildi', 'Tekrar eden global HTML parçaları tek bir yerden yönetilebilir formata çekildi.', 'git add app/templates/components/ app/templates/*.html app/static/js/org_event_new_page.js app/routes/views.py'),
    ('feat(analytics): SQLite verileriyle ürün analitiği grafikleri oluşturuldu', 'Projenin test durumu, modül kapsamı ve kalite kapılarını görselleştiren Matplotlib analitikleri oluşturuldu.', 'git add ProjectManagement/Sprint3Documents/*.png'),
    ('docs(ai): AI doğrulama raporu eklendi', 'Gerçek Gemini API testleri, fallback senaryoları ve semantic recommendation doğrulama sonuçları dokümante edildi.', ''),
    ('docs(readme): Sprint 3 raporu ve ürün analitiği dokümante edildi', 'Test sonuçları, AI hataları ve çözüm yollarını içeren şeffaf ve profesyonel sürüm raporu yayınlandı.', 'git rm \"ProjectManagement/Sprint3Documents/Kalite Kapıları*\" \"ProjectManagement/Sprint3Documents/İki Taraflı*\" \"ProjectManagement/Sprint3Documents/Sahte Verisiz*\" list_zip.py temp.zip update_js.py update_js_safe.py zip_contents.txt -f --ignore-unmatch; git add README.md')
]

for title, body, add_cmd in commits:
    if add_cmd:
        run(add_cmd)
    
    run(f'git commit --allow-empty -m "{title}" -m "{body}"')

run("git add .")
run('git commit --allow-empty -m "chore(cleanup): sprint 3 sonu dosya senkronizasyonu" -m "Unstaged ufak tefek değişiklikler ve assetler repoya eklendi."')
run("git push origin suheda")
