"""
Gemini API ile başlık, açıklama ve etiket üretir.
Her kanalın stiline göre özel prompt kullanır.
"""
import google.generativeai as genai
import json
import re


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
    Bir kanal için başlık, açıklama ve etiketler üretir.
    
    channel_config: config.py'deki kanal dict (display_name, concept, video_keywords vs)
    channel_prompts: config.py'deki CHANNEL_PROMPTS dict
    
    Returns: {"title": "...", "description": "...", "tags": [...]}
    """
    configure_gemini(api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    base_keywords = channel_config["video_keywords"]
    
    title_style = channel_prompts["title_style"]
    description_style = channel_prompts["description_style"]
    
    prompt = f"""You are a YouTube SEO expert generating metadata for a 1-hour relaxing music video.

Channel: {display_name}
Concept: {concept}
Channel keywords: {", ".join(base_keywords)}

TITLE STYLE GUIDELINES:
{title_style}

DESCRIPTION STYLE GUIDELINES:
{description_style}

Important rules:
- Title must NOT be identical to channel name
- Title should sound fresh, like a new mix or session (vary descriptors)
- Description should NOT include "Subscribe!" calls or external links
- Tags should be lowercase, comma-separated, mix of broad and specific
- Generate 15-20 tags
- All content in English

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{
  "title": "...",
  "description": "...",
  "tags": ["tag1", "tag2", ...]
}}
"""

    print(f"🤖 Gemini ile metadata üretiliyor: {display_name}")
    
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
    
    print(f"   ✓ Başlık: {data['title']}")
    print(f"   ✓ Açıklama: {len(data['description'])} karakter")
    print(f"   ✓ Etiket: {len(data['tags'])} adet")
    
    return data
