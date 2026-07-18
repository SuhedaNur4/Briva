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

GEMINI_MODEL: str = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
ANALYSIS_PROMPT_TEMPLATE: str = """Sen bir gönüllülük platformu için etkinlik ilanı kalite analisti olarak görev yapıyorsun.
Aşağıdaki etkinlik ilanını değerlendir ve YALNIZCA geçerli bir JSON nesnesi döndür.
Markdown, açıklama veya kod bloğu ekleme.

Beklenen JSON şeması:
{{
  "quality_score": <0-100 arası tam sayı>,
  "strengths": [<güçlü yönler, Türkçe, en fazla 4 madde>],
  "weaknesses": [<zayıf yönler, Türkçe, en fazla 4 madde>],
  "suggestions": [<somut iyileştirme önerileri, Türkçe, en fazla 4 madde>],
  "improved_description": "<ilanın iyileştirilmiş, gönüllüleri motive eden hali, en fazla 120 kelime>"
}}

Değerlendirme kriterleri: netlik, gönüllünün ne yapacağının açıklığı,
tarih/konum/gereksinim bilgisi, motive edici dil, hedef kitleye uygunluk.

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
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if api_key and genai is not None:
        result = _analyze_with_gemini(api_key, title, description, category, city, requirements)
        if result is not None:
            result['source'] = 'gemini'
            result['model'] = GEMINI_MODEL
            return result
    result = _fallback_analysis(title, description, category, city, requirements)
    result['source'] = 'fallback'
    result['model'] = 'rule-based'
    return result


def _analyze_with_gemini(
    api_key: str, title: str, description: str, category: str, city: str, requirements: str
) -> dict | None:
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        title=title or '-',
        category=category or '-',
        city=city or '-',
        requirements=requirements or '-',
        description=description or '-',
    )
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={'temperature': 0.4, 'response_mime_type': 'application/json'},
        )
        response = model.generate_content(prompt)
        parsed = json.loads(_strip_code_fences(response.text))
        return _validate_analysis(parsed)
    except Exception:
        return None


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`')
        if cleaned.lower().startswith('json'):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _validate_analysis(data: dict) -> dict | None:
    """Modelden dönen JSON'un beklenen şemaya uyduğunu doğrular."""
    if not isinstance(data, dict):
        return None
    score = data.get('quality_score')
    if not isinstance(score, (int, float)):
        return None
    return {
        'quality_score': max(0, min(100, int(score))),
        'strengths': _as_str_list(data.get('strengths')),
        'weaknesses': _as_str_list(data.get('weaknesses')),
        'suggestions': _as_str_list(data.get('suggestions')),
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
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    score = 40

    description = (description or '').strip()
    word_count = len(description.split())

    if title and len(title.strip()) >= 10:
        score += 10
        strengths.append('Başlık yeterince açıklayıcı.')
    else:
        weaknesses.append('Başlık çok kısa veya eksik.')
        suggestions.append('Başlığı etkinliğin amacını özetleyecek şekilde genişletin.')

    if word_count >= 40:
        score += 20
        strengths.append('Açıklama detaylı; gönüllü ne yapacağını anlayabilir.')
    elif word_count >= 15:
        score += 10
        suggestions.append('Açıklamaya gönüllünün üstleneceği somut görevleri ekleyin.')
    else:
        weaknesses.append('Açıklama çok kısa; gönüllünün rolü belirsiz.')
        suggestions.append('Etkinlikte yapılacak işleri madde madde açıklayın.')

    if category:
        score += 5
        strengths.append('Kategori bilgisi mevcut.')
    else:
        weaknesses.append('Kategori belirtilmemiş.')

    if city:
        score += 5
    else:
        weaknesses.append('Şehir/konum bilgisi eksik.')
        suggestions.append('Etkinliğin gerçekleşeceği şehir ve adresi ekleyin.')

    if requirements:
        score += 10
        strengths.append('Gönüllü gereksinimleri belirtilmiş.')
    else:
        suggestions.append('Aranan beceri veya gereksinimleri belirtin; eşleşme kalitesini artırır.')

    motivational_words = ('katkı', 'destek', 'birlikte', 'fark', 'iyilik', 'topluluk', 'gönüllü')
    if any(word in description.lower() for word in motivational_words):
        score += 10
        strengths.append('Motive edici bir dil kullanılmış.')
    else:
        suggestions.append('Gönüllüleri motive eden, sosyal etkiyi vurgulayan ifadeler ekleyin.')

    return {
        'quality_score': max(0, min(100, score)),
        'strengths': strengths[:4],
        'weaknesses': weaknesses[:4],
        'suggestions': suggestions[:4],
        'improved_description': '',
    }


def compact_analysis(analysis: dict) -> dict:
    """Issue #18'de tanımlanan kompakt formata dönüştürür: {score, warnings, suggestions}."""
    return {
        'score': analysis.get('quality_score', 0),
        'warnings': analysis.get('weaknesses', []),
        'suggestions': analysis.get('suggestions', []),
        'source': analysis.get('source', 'fallback'),
    }
