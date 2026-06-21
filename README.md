# 🌉 Briva – Yapay Zekâ Destekli Gönüllülük Platformu

Briva, gönüllüler ile sivil toplum kuruluşlarını tek bir platformda buluşturan yapay zekâ destekli bir gönüllülük sistemidir.

Amaç, gönüllülüğü daha erişilebilir hale getirerek **doğru insanı doğru sosyal etki fırsatıyla buluşturmaktır.**

Bu proje **YZTA 2026 Yapay Zekâ ve Teknoloji Atölyesi Bootcamp Hackathon’u** için geliştirilmiştir.


## 👥 Takım İsmi
Takım 122 

---

## 👤 Takım Rolleri

| İsim | Rol |
|------|-----|
| Şüheda Nur Gül | Product Owner |
| Mesut Baksı | Scrum Master |
| Tarık Sarısı | Development Team |

---

## 🌉 İsim Kökeni (Briva)

Briva ismi iki kavramdan türetilmiştir:

- **Bridge (Köprü)** → Gönüllüler ve STK’lar arasında bağlantı kurma  
- **Viva (Yaşam)** → İyiliğin ve sosyal etkinin hayatın içinde olması  

Briva bu anlamda:
> İnsanları ve iyiliği birbirine bağlayan dijital köprü

fikrini temsil eder.

---

## 🎯 Problem

Gönüllülük süreçleri şu anda parçalı ve verimsiz şekilde ilerlemektedir:

| Problem | Açıklama |
|--------|----------|
| Dağınıklık | Etkinlikler farklı kanallarda (sosyal medya vb.) |
| Eşleşme Sorunu | Gönüllüler uygun etkinliği bulamıyor |
| STK Erişim Sorunu | STK’lar doğru gönüllülere ulaşamıyor |
| Kişiselleştirme Eksikliği | Kullanıcıya özel öneri sistemi yok |

---

## 💡 Çözüm

Briva, tüm gönüllülük süreçlerini tek platformda toplar ve kullanıcıya özel öneriler sunar.

| Bileşen | Görev |
|--------|------|
| Gönüllü Profili | İlgi alanları, beceriler, uygunluk |
| STK Paneli | Etkinlik oluşturma ve başvuru yönetimi |
| AI Katmanı | Eşleştirme ve öneri sistemi |


---

## ⭐ Ürün Özellikleri

| Modül | Açıklama |
|------|----------|
| Gönüllü Profili | İlgi alanı, beceri, konum ve uygunluk bilgileri |
| STK Sistemi | Etkinlik oluşturma ve gönüllü yönetimi |
| AI Öneri Sistemi | Kişiselleştirilmiş etkinlik önerileri |
| Etkinlik Başvuru Sistemi | Gönüllülerin etkinliklere katılımı |
| Gönüllülük Takibi | Katılım geçmişi |
| Rozet Sistemi | Motivasyon |

---

## 🎯 Hedef Kitle

| Grup | Açıklama |
|------|----------|
| Gönüllüler | Sosyal sorumluluk projelerine katılmak isteyen bireyler |
| STK’lar | Gönüllü ihtiyacı olan sivil toplum kuruluşları |
| Üniversite Öğrencileri | Sosyal etki ve deneyim kazanmak isteyen gençler |
| Kurumsal Yapılar | CSR (sosyal sorumluluk) projeleri yürüten şirketler |

---

## 🏗️ Sistem Mimarisi (Yaklaşım)

Briva, modüler ve servis tabanlı bir mimari ile tasarlanmıştır.

### 🔹 Katmanlar ve Teknoloji Yaklaşımı

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| Kullanıcı Arayüzü | React | Mobil ve web uyumlu tek platform |
| Backend Servisi | Node.js + Express | REST API tabanlı ana sistem |
| AI Servisi | Python + FastAPI | Öneri ve analiz motoru |
| Veritabanı | PostgreSQL | Kullanıcı ve etkinlik verisi |
| Kimlik Doğrulama | JWT | Oturum ve erişim yönetimi |

---

## 🔌 Backend API

### 👤 Auth Servisi
| Endpoint | Açıklama |
|----------|----------|
| POST /auth/register | Kullanıcı kayıt |
| POST /auth/login | Kullanıcı giriş |
| GET /user/profile | Kullanıcı profil bilgisi |
| PUT /user/profile | Profil güncelleme |

---

### 🎯 Etkinlik Servisi
| Endpoint | Açıklama |
|----------|----------|
| POST /event | Yeni etkinlik oluştur (STK) |
| GET /events | Tüm etkinlikleri listele |
| GET /event/{id} | Etkinlik detayını getir |
| POST /event/apply | Etkinliğe başvur |

---

### 🧠 AI Servisi
| Endpoint | Açıklama |
|----------|----------|
| POST /ai/recommend | Kullanıcıya etkinlik öner |
| POST /ai/event-check | Etkinlik ilan analizi ve iyileştirme önerisi |

---

## 🧩 Product Backlog

| Öncelik | User Story |
|---------|------------|
| P1 | Kullanıcı olarak kayıt olup profil oluşturmak istiyorum |
| P1 | Gönüllü olarak bana uygun etkinlikleri görmek istiyorum |
| P1 | STK olarak etkinlik oluşturmak istiyorum |
| P1 | Etkinliklere başvuru yapabilmek istiyorum |
| P2 | AI’nın bana neden öneri verdiğini görmek istiyorum |
| P2 | Gönüllülük geçmişimi takip etmek istiyorum |
| P3 | Rozet kazanarak motivasyon sağlamak istiyorum |
| P3 | STK olarak başvuruları filtrelemek istiyorum |

---

## 🚀 MVP Kapsamı

Briva’nın ilk versiyonunda:

- Kullanıcı kayıt sistemi
- STK etkinlik oluşturma
- Etkinlik listeleme
- Basit AI tabanlı öneri sistemi
- Başvuru sistemi

bulunacaktır.

---

## 🎯 Ürün Vizyonu

Briva sadece bir etkinlik platformu değildir.

- Gönüllülüğü erişilebilir hale getirir  
- Doğru eşleşmeleri sağlar  
- Sosyal etkiyi artırır  
- Gönüllülüğü bir “yaşam yolculuğuna” dönüştürür  
