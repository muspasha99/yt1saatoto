"""
Gemini API ile başlık, açıklama ve etiket üretir.
SEO odaklı: her video için kanalın seo_keywords havuzundan rastgele
bir long-tail keyword seçilir ve title/description/tags etrafında inşa edilir.
"""
import google.generativeai as genai
import json
import re
import random


def configure_gemini(api_key):
    """Gemini API'yi yapılandır."""
    genai.configure(api_key=api_key)


def _clean_json_response(text):
    """Gemini bazen ```json ... ``` ile sarıyor, temizle."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_metadata(api_key, channel_config, channel_prompts):
    """
    Bir kanal için SEO-odaklı başlık, açıklama ve etiketler üretir.
    
    Strateji: kanalın seo_keywords havuzundan rastgele bir long-tail keyword
    seçilir, başlığın başına koyulur, açıklamanın ilk cümlesinde geçirilir,
    tag'lerde varyasyonları üretilir.
    
    Returns: {"title": "...", "description": "...", "tags": [...]}
    """
    configure_gemini(api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    seo_keywords = channel_config.get("seo_keywords", [])
    
    if not seo_keywords:
        raise Exception(
            f"❌ '{display_name}' kanalı için seo_keywords listesi boş veya eksik. "
            f"config.py'da bu alanı doldur."
        )
    
    # Bu video için rastgele bir long-tail keyword seç (SEO rotasyonu)
    primary_keyword = random.choice(seo_keywords)
    
    title_style = channel_prompts["title_style"]
    description_style = channel_prompts["description_style"]
    
    prompt = f"""You are a YouTube SEO expert generating metadata for a 1-hour music/meditation video.

Channel: {display_name}
Concept: {concept}
PRIMARY SEO KEYWORD (you MUST optimize for this exact phrase): "{primary_keyword}"

=== TITLE REQUIREMENTS (CRITICAL) ===
- The PRIMARY KEYWORD must appear at the START of the title (front-loading is essential for YouTube SEO)
- After the keyword, add 1-2 modifier words for uniqueness (e.g., "1 HOUR", "DEEP", "RELAX")
- Optionally add ONE emoji near the end
- Total length: 50-90 characters
- Title must NOT be identical to the channel name
- Style/tone notes: {title_style}

=== DESCRIPTION REQUIREMENTS (CRITICAL) ===
- The FIRST SENTENCE must contain the PRIMARY KEYWORD or a very close variant
- The first 150 characters are the most important (mobile preview)
- Length: 3-5 sentences total
- NO "Subscribe!" calls, NO external links, NO clickbait promises
- Style/tone notes: {description_style}

=== TAGS REQUIREMENTS (CRITICAL) ===
- 12-15 tags total
- First tag = the EXACT primary keyword: "{primary_keyword}"
- Next 3-4 tags = close variations of the primary keyword (rearranged words, synonyms)
- Then 4-5 long-tail tags (3+ words each, related to topic)
- Then 3-4 broad niche tags (2-3 words each)
- All lowercase, no special characters
- AVOID single-word tags (they don't rank in YouTube search)

Respond ONLY with valid JSON in this exact format (no markdown, no explanation, no code fences):
{{
  "title": "...",
  "description": "...",
  "tags": ["tag1", "tag2", ...]
}}
"""
    
    print(f"🤖 Gemini ile metadata üretiliyor: {display_name}")
    print(f"   🎯 Bu video için seçilen SEO keyword: '{primary_keyword}'")
    
    response = model.generate_content(prompt)
    raw_text = response.text
    
    # JSON'u temizle ve parse et
    cleaned = _clean_json_response(raw_text)
    
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️  Gemini cevabı parse edilemedi, ham cevap:\n{raw_text}")
        raise Exception(f"Gemini JSON hatası: {e}")
    
    # Doğrulama
    if not all(k in data for k in ["title", "description", "tags"]):
        raise Exception(f"Gemini eksik alan döndürdü: {data}")
    
    # Title YouTube'un 100 karakter sınırını aşmasın
    if len(data["title"]) > 100:
        data["title"] = data["title"][:97] + "..."
    
    # Description YouTube'un 5000 karakter sınırını aşmasın
    if len(data["description"]) > 5000:
        data["description"] = data["description"][:4997] + "..."
    
    # Tag listesi 500 karakter sınırını aşmasın
    tags = data["tags"]
    while len(",".join(tags)) > 500 and len(tags) > 5:
        tags.pop()
    data["tags"] = tags
    
    # Bilgi yazdır
    print(f"   ✓ Başlık: {data['title']}")
    print(f"   ✓ Açıklama: {len(data['description'])} karakter")
    print(f"   ✓ Etiket: {len(data['tags'])} adet")
    print(f"   ✓ Birincil tag: '{data['tags'][0]}' " + 
          ("✅" if data["tags"][0].lower() == primary_keyword.lower() else "⚠️ keyword'le birebir değil"))
    
    return data
