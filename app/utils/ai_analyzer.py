"""AI Etkinlik Analizörü (Sprint 2).

Etkinlik başlığı ve açıklamasını analiz ederek STK'lara kalite puanı,
güçlü/zayıf yönler ve iyileştirilmiş bir açıklama önerisi sunar.

Birincil motor: Google Gemini API (GEMINI_API_KEY ortam değişkeni ile).
API anahtarı yoksa veya istek başarısız olursa kural tabanlı bir
fallback analiz devreye girer; böylece sistem her koşulda çalışır kalır.
"""
from __future__ import annotations

import json
import os

try:
    import google.generativeai as genai  # issue #18: google-generativeai paketi
except ImportError:  # paket kurulu değilse kural tabanlı fallback devrede kalır
    genai = None

GEMINI_MODEL: str = os.environ.get('GEMINI_GENERATION_MODEL', 'gemini-3.5-flash')
GEMINI_EMBEDDING_MODEL: str = os.environ.get('GEMINI_EMBEDDING_MODEL', 'models/gemini-embedding-2')

# API key modül yüklendiğinde bir kez okunup configure edilir.
# Her fonksiyon çağrısında os.environ lookup + genai.configure() tekrarı önlenir.
_API_KEY: str = os.environ.get('GEMINI_API_KEY', '').strip()
_GEMINI_READY: bool = bool(_API_KEY and genai is not None)
if _GEMINI_READY:
    genai.configure(api_key=_API_KEY)

ANALYSIS_PROMPT_TEMPLATE: str = """Sen bir gönüllülük platformu için uzman etkinlik ilanı kalite analisti olarak görev yapıyorsun.
Aşağıdaki etkinlik ilanını değerlendir ve YALNIZCA geçerli bir JSON nesnesi döndür.
Markdown, açıklama veya kod bloğu ekleme.

Beklenen JSON şeması:
{{
  "quality_score": <0-100 arası tam sayı>,
  "missing_info": [<eksik bilgilerin listesi, Türkçe>],
  "missing_info_reasoning": "<bu eksiklerin gönüllü katılımını neden düşüreceğine dair mantıklı açıklama, Türkçe>",
  "concrete_suggestions": [<somut ve detaylı iyileştirme önerileri, Türkçe>],
  "title_suggestion": "<daha çekici ve net bir başlık önerisi>",
  "requirements_suggestion": "<gönüllülerden beklenen gereksinimlerin daha net ifade edilmiş hali>",
  "improved_description": "<ilanın baştan aşağı yeniden yazılmış, eksiksiz, doğrudan kopyala-yapıştır kullanılabilecek mükemmel hali>"
}}

Değerlendirme kriterleri: netlik, gönüllünün ne yapacağının açıklığı, tarih/konum/gereksinim bilgisi, motive edici dil, hedef kitleye uygunluk.

Etkinlik ilanı:
Başlık: {title}
Kategori: {category}
Şehir: {city}
Gereksinimler: {requirements}
Açıklama: {description}
"""


def analyze_event_text(
    title: str,
    description: str = '',
    category: str = '',
    city: str = '',
    requirements: str = '',
) -> dict:
    """Etkinlik metnini analiz eder. Gemini erişilemezse fallback kullanır."""
    if _GEMINI_READY:
        result = _analyze_with_gemini(title, description, category, city, requirements)
        if result is not None:
            result['source'] = 'gemini'
            result['model'] = GEMINI_MODEL
            result['ai_generated'] = True
            result['fallback_used'] = False
            return result
    result = _fallback_analysis(title, description, category, city, requirements)
    result['source'] = 'fallback'
    result['model'] = 'rule-based'
    result['ai_generated'] = False
    result['fallback_used'] = True
    return result


def _analyze_with_gemini(
    title: str, description: str, category: str, city: str, requirements: str
) -> dict | None:
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        title=title or '-',
        category=category or '-',
        city=city or '-',
        requirements=requirements or '-',
        description=description or '-',
    )
    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={'temperature': 0.4, 'response_mime_type': 'application/json'},
        )
        response = model.generate_content(prompt)
        parsed = json.loads(_strip_code_fences(response.text))
        return _validate_analysis(parsed)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`')
        if cleaned.lower().startswith('json'):
            cleaned = cleaned[4:]
    return cleaned.strip()

APPLICANT_EVALUATION_PROMPT = """Sen bir STK (Sivil Toplum Kuruluşu) için aday değerlendirme asistanısın.
Aşağıda verilen Gönüllü Profilini ve Etkinlik Kriterlerini dikkatle analiz et. Adayın etkinliğe ne kadar uygun olduğunu anlamsal (semantic) olarak değerlendir.

Gönüllü Profili:
- Biyografi/Hakkında: {bio}
- İlgi Alanları: {interests}
- Beceriler: {skills}
- Şehir: {user_city}

Etkinlik Kriterleri:
- Başlık: {event_title}
- Açıklama: {event_desc}
- Gereksinimler: {event_reqs}
- Kategori: {event_category}
- Şehir: {event_city}

YALNIZCA aşağıdaki JSON formatında cevap ver. Herhangi bir markdown veya açıklama metni ekleme.
Gaps kısmına, etkinlik kriterlerinde istenen ancak gönüllü profilinde doğrulanamayan gereksinimleri yaz.
Strengths kısmına, adayın etkinliğe uygun güçlü yönlerini yaz.

{{
  "match_score": <0 ile 100 arası tamsayı>,
  "summary": "<2-3 cümlelik profesyonel aday özeti>",
  "strengths": ["<güçlü yön 1>", "<güçlü yön 2>"],
  "gaps": ["<eksik yön 1>", "<eksik yön 2>"],
  "recommendation": "<strong_match, possible_match veya weak_match>"
}}
"""

def evaluate_applicant_with_gemini(applicant_data: dict, event_data: dict) -> dict | None:
    """Gemini API kullanarak aday ve etkinlik arasındaki uygunluğu semantik olarak değerlendirir."""
    if not _GEMINI_READY:
        return None
    
    prompt = APPLICANT_EVALUATION_PROMPT.format(
        bio=applicant_data.get('bio') or 'Belirtilmedi',
        interests=', '.join(applicant_data.get('interests') or ['Belirtilmedi']),
        skills=', '.join(applicant_data.get('skills') or ['Belirtilmedi']),
        user_city=applicant_data.get('city') or 'Belirtilmedi',
        event_title=event_data.get('title') or 'Belirtilmedi',
        event_desc=event_data.get('description') or 'Belirtilmedi',
        event_reqs=event_data.get('requirements') or 'Belirtilmedi',
        event_category=event_data.get('category') or 'Belirtilmedi',
        event_city=event_data.get('city') or 'Belirtilmedi'
    )
    
    try:
        if _API_KEY:
            genai.configure(api_key=_API_KEY)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={'temperature': 0.3, 'response_mime_type': 'application/json'},
        )
        response = model.generate_content(prompt)
        parsed = json.loads(_strip_code_fences(response.text))
        
        # Validasyon
        if not isinstance(parsed, dict) or 'match_score' not in parsed:
            raise ValueError("Invalid format from Gemini")
            
        return {
            'match_score': max(0, min(100, int(parsed.get('match_score', 0)))),
            'summary': str(parsed.get('summary', '')).strip(),
            'strengths': _as_str_list(parsed.get('strengths')),
            'gaps': _as_str_list(parsed.get('gaps')),
            'recommendation': str(parsed.get('recommendation', 'possible_match')).strip(),
            'source': 'gemini',
            'ai_generated': True,
            'fallback_used': False
        }
    except Exception as e:
        # Fallback response
        return {
            'match_score': 50,
            'summary': 'Yapay zeka analizi şu anda gerçekleştirilemiyor.',
            'strengths': [],
            'gaps': [],
            'recommendation': 'possible_match',
            'source': 'fallback',
            'ai_generated': False,
            'fallback_used': True
        }

def get_embedding(text: str) -> list[float] | None:
    """Metin için Gemini Embedding API'sini kullanarak vektör döndürür."""
    if not _GEMINI_READY or not text.strip():
        return None
    try:
        if _API_KEY:
            genai.configure(api_key=_API_KEY)
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        return None

def _validate_analysis(data: dict) -> dict | None:
    """Modelden dönen JSON'un beklenen şemaya uyduğunu doğrular."""
    if not isinstance(data, dict):
        return None
    score = data.get('quality_score')
    if not isinstance(score, (int, float)):
        return None
    return {
        'quality_score': max(0, min(100, int(score))),
        'missing_info': _as_str_list(data.get('missing_info')),
        'missing_info_reasoning': str(data.get('missing_info_reasoning') or '').strip(),
        'concrete_suggestions': _as_str_list(data.get('concrete_suggestions')),
        'title_suggestion': str(data.get('title_suggestion') or '').strip(),
        'requirements_suggestion': str(data.get('requirements_suggestion') or '').strip(),
        'improved_description': str(data.get('improved_description') or '').strip(),
    }


def _as_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:4]


# ---------------------------------------------------------------------------
# Kural tabanlı fallback — API anahtarı yokken de sistemin çalışmasını sağlar
# ---------------------------------------------------------------------------

def _fallback_analysis(
    title: str, description: str, category: str, city: str, requirements: str
) -> dict:
    missing_info: list[str] = []
    concrete_suggestions: list[str] = []
    score = 40
    title_suggestion = ""
    requirements_suggestion = ""

    description = (description or '').strip()
    word_count = len(description.split())

    if title and len(title.strip()) >= 10:
        score += 10
    else:
        missing_info.append('Başlık çok kısa veya eksik.')
        concrete_suggestions.append('Başlığı etkinliğin amacını özetleyecek şekilde genişletin.')
        title_suggestion = f"{category or 'Gönüllülük'} Etkinliği" if not title else f"{title} (Daha açıklayıcı olmalı)"

    if word_count >= 40:
        score += 20
    elif word_count >= 15:
        score += 10
        concrete_suggestions.append('Açıklamaya gönüllünün üstleneceği somut görevleri ekleyin.')
    else:
        missing_info.append('Açıklama çok kısa; gönüllünün rolü belirsiz.')
        concrete_suggestions.append('Etkinlikte yapılacak işleri madde madde açıklayın.')

    if category:
        score += 5
    else:
        missing_info.append('Kategori belirtilmemiş.')

    if city:
        score += 5
    else:
        missing_info.append('Şehir/konum bilgisi eksik.')
        concrete_suggestions.append('Etkinliğin gerçekleşeceği şehir ve adresi ekleyin.')

    if requirements:
        score += 10
    else:
        missing_info.append('Gönüllü gereksinimleri belirtilmemiş.')
        concrete_suggestions.append('Aranan beceri veya gereksinimleri belirtin; eşleşme kalitesini artırır.')
        requirements_suggestion = "İletişim becerisi, takım çalışmasına yatkınlık vb."

    motivational_words = ('katkı', 'destek', 'birlikte', 'fark', 'iyilik', 'topluluk', 'gönüllü')
    if any(word in description.lower() for word in motivational_words):
        score += 10
    else:
        concrete_suggestions.append('Gönüllüleri motive eden, sosyal etkiyi vurgulayan ifadeler ekleyin.')

    return {
        'quality_score': max(0, min(100, score)),
        'missing_info': missing_info[:4],
        'missing_info_reasoning': 'Bu bilgilerin eksik olması gönüllülerin etkinliğe olan güvenini ve başvuru oranını doğrudan düşürür.',
        'concrete_suggestions': concrete_suggestions[:4],
        'title_suggestion': title_suggestion,
        'requirements_suggestion': requirements_suggestion,
        'improved_description': description,
    }


def compact_analysis(analysis: dict) -> dict:
    """Issue #18'de tanımlanan kompakt formata dönüştürür: {score, warnings, suggestions}."""
    return {
        'score': analysis.get('quality_score', 0),
        'warnings': analysis.get('missing_info', []),
        'suggestions': analysis.get('concrete_suggestions', []),
        'source': analysis.get('source', 'fallback'),
    }

EXPLANATION_PROMPT = """Sen Briva'nın gönüllülük eşleştirme asistanısın.

Aşağıdaki gerçek kullanıcı bilgilerine dayanarak bu etkinliğin gönüllü için neden uygun olabileceğini 2-3 kısa cümleyle açıkla.
SADECE verilen bilgilere dayan. Kullanıcı hakkında verilmemiş hiçbir özellik uydurma.

Kullanıcı:
{user_context}

Etkinlik:
{event_context}

Açıklama doğrudan kullanıcıya "sen" diliyle hitap etsin (Örn: "...ilgini çekebilir", "...tecrüben sana avantaj sağlar").
"""

def explain_recommendation_with_gemini(user_context: str, event_context: str) -> dict:
    """Yapay Zeka ile kullanıcının etkinliğe neden uygun olduğunu açıklar."""
    if not _GEMINI_READY or not user_context.strip() or not event_context.strip():
        return {'explanation': 'Profilinize ve tercihlerinize genel olarak uygun bir etkinlik.', 'ai_generated': False, 'fallback_used': True}
    
    prompt = EXPLANATION_PROMPT.format(user_context=user_context, event_context=event_context)
    try:
        if _API_KEY:
            genai.configure(api_key=_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL, generation_config={'temperature': 0.3})
        response = model.generate_content(prompt)
        text = response.text.strip()
        if not text:
            raise ValueError("Empty response")
        return {'explanation': text, 'ai_generated': True, 'fallback_used': False}
    except Exception as e:
        return {'explanation': 'Profilinize ve aranan niteliklere göre size uygun görüldü.', 'ai_generated': False, 'fallback_used': True}
