"""
Groq API ile başlık, açıklama ve etiket üretir.
Gemini_handler yerine kullanılır — aynı fonksiyon imzaları korundu.
Model: llama-3.3-70b-versatile (ücretsiz, 14.400 istek/gün)
"""
import os
import time
import json
import re
import random
from groq import Groq


def _get_api_keys():
    """Mevcut Groq API key'lerini döner."""
    keys = []
    for env_var in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
        key = os.environ.get(env_var)
        if key:
            keys.append(key)
    if not keys:
        raise Exception("Hiçbir GROQ_API_KEY bulunamadı!")
    return keys


def _call_groq(prompt, system=None, max_retries_per_key=3):
    """
    Groq API çağrısı yapar.
    Rate limit hatalarında bekler, sonra diğer key'e geçer.
    """
    keys = _get_api_keys()
    print(f"   🔑 {len(keys)} Groq key mevcut")

    last_error = None
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for key_idx, api_key in enumerate(keys):
        client = Groq(api_key=api_key)

        for attempt in range(max_retries_per_key):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.85,
                )
                if key_idx > 0:
                    print(f"   ✅ Key {key_idx + 1} ile başarılı")
                return response.choices[0].message.content
            except Exception as e:
                err = str(e)
                if "429" in err or "rate" in err.lower() or "quota" in err.lower() or "timeout" in err.lower():
                    if attempt < max_retries_per_key - 1:
                        wait = 10 * (attempt + 1)
                        print(f"   ⏳ Key {key_idx + 1} rate limit, {wait}s bekleniyor...")
                        time.sleep(wait)
                    else:
                        print(f"   ⚠️ Key {key_idx + 1} tükendi, sonraki key deneniyor...")
                        last_error = e
                        break
                else:
                    raise

    raise Exception(f"Tüm Groq key'leri başarısız: {last_error}")


def _clean_json_response(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_metadata(api_key, channel_config, channel_prompts, thumbnail_path=None):
    """
    SEO odaklı metadata üretir.
    thumbnail_path parametresi uyumluluk için korundu (kullanılmıyor).
    """
    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    seo_keywords = channel_config.get("seo_keywords", [])

    if not seo_keywords:
        raise Exception(
            f"❌ '{display_name}' için seo_keywords boş. config.py'ı güncelle."
        )

    primary_keyword = random.choice(seo_keywords)
    title_style = channel_prompts["title_style"]
    description_style = channel_prompts["description_style"]

    system = "You are a YouTube SEO expert. Always respond with valid JSON only. No markdown, no explanation, no extra text."

    prompt = f"""Generate YouTube metadata for a 1-hour music video.

Channel: {display_name}
Concept: {concept}
PRIMARY SEO KEYWORD (optimize for this): "{primary_keyword}"

=== TITLE REQUIREMENTS ===
- PRIMARY KEYWORD must appear at the START of the title (front-loading)
- Add 1-2 modifier words after that naturally fit the keyword
- ONE emoji near the end (optional)
- 50-90 characters total
- Must NOT be identical to the channel name
- Style/tone notes: {title_style}

=== DESCRIPTION REQUIREMENTS ===
- First sentence MUST contain the PRIMARY KEYWORD or close variant
- First 150 characters are most important (mobile preview)
- 3-5 sentences total
- NO "Subscribe!" calls, NO external links
- Style/tone notes: {description_style}
- At the very END, add exactly 3-5 hashtags like: #lofi #studymusic #relaxing
- Hashtags must match the primary keyword and niche
- Hashtags go on a new line at the end

=== TAGS REQUIREMENTS ===
- 12-15 tags total
- First tag = exact PRIMARY KEYWORD: "{primary_keyword}"
- Next 3-4 = close variations of primary keyword
- Then 4-5 long-tail related tags (3+ words each)
- Then 3-4 broad niche tags (2-3 words)
- All lowercase, no special characters
- NO single-word tags

Respond ONLY with valid JSON:
{{
  "title": "...",
  "description": "...",
  "tags": ["tag1", "tag2", ...]
}}"""

    print(f"🤖 Groq ile metadata üretiliyor: {display_name}")
    print(f"   🎯 SEO keyword: '{primary_keyword}'")

    raw_text = _call_groq(prompt, system)
    cleaned = _clean_json_response(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️  Groq parse hatası:\n{raw_text}")
        raise Exception(f"Groq JSON hatası: {e}")

    if not all(k in data for k in ["title", "description", "tags"]):
        raise Exception(f"Groq eksik alan döndürdü: {data}")

    if len(data["title"]) > 100:
        data["title"] = data["title"][:97] + "..."
    if len(data["description"]) > 5000:
        data["description"] = data["description"][:4997] + "..."

    desc = data["description"]
    if "#" not in desc:
        hashtags = " ".join(f"#{tag.replace(' ', '')}" for tag in data["tags"][:5])
        data["description"] = desc.strip() + f"\n\n{hashtags}"

    tags = data["tags"]
    while len(",".join(tags)) > 500 and len(tags) > 5:
        tags.pop()
    data["tags"] = tags

    print(f"   ✓ Başlık: {data['title']}")
    print(f"   ✓ Açıklama: {len(data['description'])} karakter")
    print(f"   ✓ Etiket: {len(data['tags'])} adet")

    return data


def generate_short_text(api_key, channel_config, channel_prompts):
    """
    Shorts videosu için kısa overlay text üretir.
    Max 30 karakter.
    """
    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    short_sentences = channel_config.get("short_sentences", [])
    short_quotes = channel_config.get("short_quotes", [])

    system = "You are a creative copywriter. Respond with the text only. No quotes, no explanation, nothing else."

    prompt = f"""Write overlay text for a YouTube Shorts video.

Channel: {display_name}
Concept: {concept}

Reference sentences for this channel's vibe:
{chr(10).join(f'- {s}' for s in short_sentences[:8])}

Reference quotes:
{chr(10).join(f'- {q}' for q in short_quotes[:4])}

Rules:
- Write ONE short text to display on screen
- MAX 30 characters (count carefully)
- Can be an original sentence OR a short famous quote
- Must match the channel's vibe and concept
- No hashtags, no emojis
- Produce something DIFFERENT every time
- Do NOT repeat the reference sentences word for word

Respond ONLY with the text itself.
Examples: "Lock in. No excuses." / "Breathe. Just breathe." / "Deep work. Deep life."
"""

    # Groq'ta rate limit çok geniş, beklemeye gerek yok
    raw_text = _call_groq(prompt, system)
    text = raw_text.strip().strip('"').strip("'")

    if len(text) > 30:
        text = text[:30].rsplit(" ", 1)[0]

    print(f"   ✏️  Short text: '{text}' ({len(text)} karakter)")
    return text
